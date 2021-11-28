import os, sqlite3
from SPARQLWrapper import SPARQLWrapper, JSON

LOCAL_WIKIPEDIA_ROOT = "http://localhost:8888/wikipedia_en_movies_nopic_2021-10/A"

# Fetches a list of all IMDB tconsts + titles in the database
def get_imdb_movies():
    assert os.path.exists("imdb.db")

    conn = sqlite3.connect("imdb.db")
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT tconst, title from titles")
        return list(cur.fetchall())


# Returns a function
def generate_sparql_executor():
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

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
    movie_reviews = {}
    for movie in movies:
        if "The Incredible Hulk" in movie[1]:
            tconst, title, url = lookup_movie(movie)

            print(url)
