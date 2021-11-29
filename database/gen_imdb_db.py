import os, wget, gzip, shutil, sqlite3, glob, tqdm, requests, backoff, urllib, pickle
import pandas as pd

"""
This script generates a file imdb.db with the following two tables, keyed by IMDB IDs:
- titles: List of IMDB movies 
- names: List of IMDB-registered people (actors, directors, etc)

Usage: python gen_imdb_db.py
"""

# Downloads/extracts appropiate IMDB files
def download_files():
    LINKS = {
        "names.tsv": "https://datasets.imdbws.com/name.basics.tsv.gz",
        "akas.tsv": "https://datasets.imdbws.com/title.akas.tsv.gz",
        "basics.tsv": "https://datasets.imdbws.com/title.basics.tsv.gz",
        "crew.tsv": "https://datasets.imdbws.com/title.crew.tsv.gz",
        "principals.tsv": "https://datasets.imdbws.com/title.principals.tsv.gz",
        "ratings.tsv": "https://datasets.imdbws.com/title.ratings.tsv.gz",
    }

    # Deletes all existing downloads
    def delete_downloads():
        files = list(glob.glob("*.tsv.gz"))
        files.extend(list(glob.glob("*.tmp")))
        for file in files:
            os.remove(file)

    delete_downloads()
    for tsvname, link in LINKS.items():
        # Download the file
        print(f"\nDownloading {tsvname} from {link}")
        archivename = wget.download(link)

        # Extract the file
        print(f"\nExtracting {archivename} to {tsvname}")
        with gzip.open(archivename, "rb") as archive:
            with open(tsvname, "wb") as tsv:
                shutil.copyfileobj(archive, tsv)

    delete_downloads()


# Loads data from TSV files and produces two dataframes with movie and name data respectively
def load_data():

    # Titles
    def get_titles():
        titles = pd.read_csv("basics.tsv", sep="\t", low_memory=False)
        titles = titles.set_index("tconst")
        titles = titles[titles.titleType == "movie"]
        titles = titles.replace(to_replace="\\N", value="0")
        titles.startYear = pd.to_numeric(titles.startYear)
        titles = titles[titles.startYear > 1990]
        titles.runtimeMinutes = pd.to_numeric(titles.runtimeMinutes)
        titles = titles[titles.runtimeMinutes > 45]
        titles = titles[
            ["primaryTitle", "isAdult", "startYear", "runtimeMinutes", "genres"]
        ]
        titles.columns = ["title", "adult", "year", "runtime", "genres"]

        return titles

    # Ratings
    def get_ratings():
        # Ratings
        ratings = pd.read_csv("ratings.tsv", sep="\t", low_memory=False)
        ratings = ratings.set_index("tconst")
        ratings.columns = ["rating", "ratingVotes"]

        return ratings

    # Akas
    def get_akas():
        akas = pd.read_csv("akas.tsv", sep="\t", low_memory=False)
        akas = akas.set_index("titleId")
        akas.index.name = "tconst"
        akas = akas[akas.region.isin({"US", "XNA", "XWW"})]
        akas = akas[~akas.index.duplicated(keep="first")]
        akas = akas.replace(to_replace="\\N", value="")
        akas = akas[["title", "region", "language", "types"]]

        return akas

    # Crew
    def get_crew():
        crew = pd.read_csv("crew.tsv", sep="\t", low_memory=False).set_index("tconst")
        crew = crew.replace(to_replace="\\N", value="")

        return crew

    # Names
    def get_names():
        # Names
        names = pd.read_csv("names.tsv", sep="\t", low_memory=False).set_index("nconst")
        names.columns = ["name", "birthYear", "deathYear", "profession", "titles"]

        return names

    # Principals
    def get_principals():
        # Principals
        principals = pd.read_csv("principals.tsv", sep="\t", low_memory=False)
        principals = principals.replace(to_replace="\\N", value="")

        return principals

    # Load and merge datasets
    print("\nLoading data files into memory...")
    titles, akas, crew, ratings, names = (
        get_titles(),
        get_akas(),
        get_crew(),
        get_ratings(),
        get_names(),
    )

    print("\nBuilding dataframes...")

    # Merge with region info from akas
    titles = titles[titles.index.isin(akas.index)]
    titles = titles.merge(
        akas[["region"]], left_index=True, right_index=True, how="inner"
    )

    # Merge with crew info
    titles = titles.merge(crew, left_index=True, right_index=True, how="inner")

    # Merge with ratings
    titles = titles.merge(ratings, left_index=True, right_index=True, how="inner")

    return titles, names


# Downloads posters for every title in the dataframe
def fetch_posters(titles, api_key):
    TMDB_API_URL = "https://api.themoviedb.org/3/movie/{}?api_key={}"
    TMDB_ROOT_POSTER_URL = "https://image.tmdb.org/t/p/w200"
    DEFAULT_POSTER_URL = (
        "https://i.pinimg.com/736x/b6/01/18/b6011825cf909d54d93145b53bdb0bfb.jpg"
    )

    # Function to fetch a single poster URL
    @backoff.on_exception(backoff.expo, urllib.error.HTTPError)
    def fetch_poster_url(tconst):
        result = requests.get(TMDB_API_URL.format(tconst, api_key)).json()
        if "poster_path" in result and result["poster_path"] != None:
            return f"{TMDB_ROOT_POSTER_URL}{result['poster_path']}"
        return DEFAULT_POSTER_URL

    # Load cache if it exists
    posters = []
    cache_hits = 0
    if os.path.exists("posters.p"):
        with open("posters.p", "rb") as f:
            posters = pickle.load(f)

    # Get URLs
    print("Downloading poster URLs...")
    titles_bar = tqdm.tqdm(titles.index)
    for i, tconst in enumerate(titles_bar):

        # posters[i] already exists in cache if i < len(posters)
        if i < len(posters):
            assert posters[i] is not None
            cache_hits += 1
            continue

        posters.append(fetch_poster_url(tconst))

        # Cache write
        if i % 100 == 0 or i == len(titles.index) - 1:
            with open("posters.p", "wb") as f:
                pickle.dump(posters, f)

        titles_bar.set_postfix({"Cache hits": cache_hits})

    # Update dataframe
    titles = titles.copy()
    titles["poster"] = posters

    return titles


# Generates a Sqlite3 database for the movie/name data
def make_db(titles, names):

    print("\nBuilding database...")

    # Delete database if it exists
    if os.path.exists("imdb.db"):
        os.remove("imdb.db")

    # Write titles (list of movies) and names (to allow lookup of movies with the same people)
    conn = sqlite3.connect("imdb.db")
    titles.to_sql("titles", conn)
    names.to_sql("names", conn)

    conn.close()


# Executes a simple test query against the database to make sure it looks alright
def test_db():
    TEST_QUERY = "SELECT * from titles WHERE title LIKE '%Hulk'"

    print(f"\nTesting database with query {TEST_QUERY}")

    conn = sqlite3.connect("imdb.db")

    with conn:
        cur = conn.cursor()
        cur.execute("SELECT * from titles WHERE title LIKE '%Hulk'")
        rows = cur.fetchall()

        print("Results:")
        for row in rows:
            print(f"\t{row}")


# Deletes .tsv files downloaded from IMDB
def delete_tsvs():
    for file in glob.glob("*.tsv"):
        os.remove(file)


if __name__ == "__main__":

    download_posters = (
        input("Download movie posters? This might take a long time! y/N\n> ")
        .strip()
        .lower()
    )
    api_key = None
    if len(download_posters) == 0:
        download_posters = "n"
    elif download_posters == "y":
        api_key = input("API key for TMDB (themoviedb.org)\n> ").strip()
    elif download_posters not in ["y", "n"]:
        print("Invalid input!")
        exit(1)

    # download_files()
    # titles, names = load_data()
    titles = pd.read_csv("titles.csv")

    # optionally fetch posters
    if download_posters == "y":
        titles = fetch_posters(titles, api_key)

    make_db(titles, names)
    test_db()
    delete_tsvs()
