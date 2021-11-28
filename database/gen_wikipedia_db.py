import os, sqlite3
from SPARQLWrapper import SPARQLWrapper, JSON

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
            return (tconst, title, result["results"]["bindings"][-1]["wppage"]["value"])
        except Exception as e:
            return (tconst, title, None)

    return lookup_movie


if __name__ == "__main__":
    movies = get_imdb_movies()

    lookup_movie = generate_sparql_executor()

    for movie in movies:
        if "Hulk" in movie[1]:
            print(lookup_movie(movie))
