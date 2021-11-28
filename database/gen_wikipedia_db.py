import os, sqlite3, requests, pickle, backoff, urllib
from bs4 import BeautifulSoup
from SPARQLWrapper import SPARQLWrapper, JSON
from tqdm import tqdm


LOCAL_WIKIPEDIA_ROOT = "http://localhost:8888/wikipedia_en_movies_nopic_2021-10/A"

# Fetches a list of all IMDB tconsts + titles in the database
def get_imdb_movies():
    assert os.path.exists("imdb.db")

    conn = sqlite3.connect("imdb.db")
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT tconst, title from titles")
        return list(cur.fetchall())


# Returns a function that executes IMDB ID lookup queries against Wikidata
def generate_sparql_executor():
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

    @backoff.on_exception(backoff.expo, urllib.error.HTTPError)
    def lookup_movie(movie):
        tconst, title = movie
        query = f"""
            SELECT ?wppage WHERE {{
            ?subject wdt:P345 '{tconst}' . 
            ?wppage schema:about ?subject .
            FILTER(contains(str(?wppage),'//en.wikipedia'))
        }}
        """.strip()

        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)

        result = sparql.query().convert()

        try:
            remote_url = result["results"]["bindings"][-1]["wppage"]["value"]
            leaf = remote_url.split("/")[-1]
            local_url = f"{LOCAL_WIKIPEDIA_ROOT.rstrip('/')}/{leaf}"

            return (tconst, title, local_url)
        except Exception as e:
            return (tconst, title, None)

    return lookup_movie


if __name__ == "__main__":
    # Get all movie IDs
    movies = get_imdb_movies()

    # Get our SPARQL executor
    lookup_movie = generate_sparql_executor()

    # Lookup each movie, and store the reviews section of it locally
    # This will probably consume a lot of RAM
    # We'll make sure to load anything cached to disk in case this script is being re-run
    movie_urls = {}
    if os.path.exists("movie_urls.p"):
        with open("movie_urls.p", "rb") as f:
            movie_urls = pickle.load(f)
    movie_responses = {}
    if os.path.exists("movie_responses.p"):
        with open("movie_responses.p", "rb") as f:
            movie_responses = pickle.load(f)
    url_cache_hits = 0
    response_cache_hits = 0

    movies_bar = tqdm(movies)
    for i, movie in enumerate(movies_bar):

        tconst, title = movie
        url = None

        # Check if URL is in our cache
        if tconst in movie_urls:
            # print(f"URL for {tconst} is cached: {movie_urls[tconst]}")
            url = movie_urls[tconst]
            url_cache_hits += 1
        # Otherwise do SPARQL lookup to get the URL
        else:
            tconst, title, url = lookup_movie(movie)
            movie_urls[tconst] = url

        # Check if we have a critic response in our cache
        response_text = None
        if tconst in movie_responses and len(str(movie_responses[tconst])) > 20:
            response_text = movie_responses[tconst]
            response_cache_hits += 1
        # Otherwise query """Wikipedia""" if we have a URL
        elif url is not None:
            html = requests.get(url).text
            soup = BeautifulSoup(html, "html.parser")
            sections = soup.find_all("summary")

            # Find the critical response/reviews section
            # Usually they are near the end of the document
            response_section = None
            for section in sections:
                text = section.get_text().lower()
                if "critical" in text or "response" in text:
                    response_section = section

            # Now we can just extract the text of the critical response section, and save this info
            if response_section is not None:
                response_text = response_section.parent.text
                movie_responses[tconst] = response_text

        # Update our cache every 100 lookups
        if i % 100 == 0:
            with open("movie_urls.p", "wb") as f:
                pickle.dump(movie_urls, f)
            with open("movie_responses.p", "wb") as f:
                pickle.dump(movie_responses, f)

        # Update progress bar with cache hit rate
        movies_bar.set_postfix(
            {"URL cache": url_cache_hits, "Response cache": response_cache_hits}
        )
