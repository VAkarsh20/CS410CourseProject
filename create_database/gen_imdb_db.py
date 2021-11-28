import os, wget, gzip, shutil, sqlite3
from numpy import left_shift
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
        os.system("rm *.tsv.gz >/dev/null 2>&1")
        os.system("rm *.tmp >/dev/null 2>&1")

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
    os.system("rm *.tsv >/dev/null 2>&1")


if __name__ == "__main__":
    # download_files()
    titles, names = load_data()
    make_db(titles, names)
    test_db()
    delete_tsvs()
