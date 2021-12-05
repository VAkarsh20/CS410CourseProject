from flask import Flask, request, g
import sqlite3, pickle

# Change these if you are using different locations for the data files!
IMDB_DB = "imdb.db"
WIKIPEDIA_DB = "wikipedia.p"

app = Flask("app")

# GET /movie?tconst=<some tconst>` returns information about a single movie,
# including its title, poster, and other metadata.
@app.route("/movie")
def get_movie():
    # Invalid request
    if "tconst" not in request.args:
        return "You need to include a tconst!", 400

    # Get movie identifier
    tconst = request.args["tconst"]

    # Lookup and return the movie
    try:
        return lookup_movie(tconst), 200
    except:
        return "Oops!", 500


@app.route("/similar")
def get_similar():
    # Invalid request
    if "tconst" not in request.args or (
        "by" in request.args
        and request.args["by"].lower() not in ["directorwriter", "genre"]
    ):
        return "Invalid request!", 400

    # Extract title ID
    tconst = request.args["tconst"]

    # Extract filters (directors, writers, genres)
    by = None if "by" not in request.args else request.args["by"]

    _, wikipedia = get_dbs()
    return wikipedia[tconst]


# Dummy endpoint for /movie which doesn't require a database
@app.route("/dummy_movie")
def get_dummy_movie():
    return {
        "adult": False,
        "directorNames": ["Justin Lin"],
        "directors": ["nm0510912"],
        "genres": ["Action", "Crime", "Thriller"],
        "poster": "https://image.tmdb.org/t/p/w200/cm2ffqb3XovzA5ZSzyN3jnn8qv0.jpg",
        "rating": 6.0,
        "ratingVotes": 259332,
        "region": "US",
        "runtime": 104,
        "tconst": "tt0463985",
        "title": "The Fast and the Furious: Tokyo Drift",
        "writerNames": ["Chris Morgan"],
        "writers": ["nm0604555"],
        "year": 2006,
    }, 200


# Dummy endpoint for /similar which doesn't require a database
@app.route("/dummy_similar")
def get_dummy_similar():
    return {
        "all": [
            {
                "adult": False,
                "directorNames": ["Dominic Sena"],
                "directors": ["nm0784061"],
                "genres": ["Action", "Crime", "Thriller"],
                "poster": "https://image.tmdb.org/t/p/w200/lFsJJjnGcNhewSIM9XBTaHsI2et.jpg",
                "rating": 6.5,
                "ratingVotes": 269640,
                "region": "US",
                "runtime": 118,
                "tconst": "tt0187078",
                "title": "Gone in 60 Seconds",
                "writerNames": ["H.B. Halicki", "Scott Rosenberg"],
                "writers": ["nm0355181", "nm0003298"],
                "year": 2000,
            },
            {
                "adult": False,
                "directorNames": ["Rob Cohen"],
                "directors": ["nm0003418"],
                "genres": ["Action", "Crime", "Thriller"],
                "poster": "https://image.tmdb.org/t/p/w200/gqY0ITBgT7A82poL9jv851qdnIb.jpg",
                "rating": 6.8,
                "ratingVotes": 370334,
                "region": "US",
                "runtime": 106,
                "tconst": "tt0232500",
                "title": "The Fast and the Furious",
                "writerNames": [
                    "Ken Li",
                    "Gary Scott Thompson",
                    "Erik Bergquist",
                    "David Ayer",
                ],
                "writers": ["nm0508446", "nm0860155", "nm0074980", "nm0043742"],
                "year": 2001,
            },
            {
                "adult": False,
                "directorNames": ["Ron Howard"],
                "directors": ["nm0000165"],
                "genres": ["Action", "Biography", "Drama"],
                "poster": "https://image.tmdb.org/t/p/w200/uWcMgxO3p3qwVFUxsRz1HbTzGvT.jpg",
                "rating": 8.1,
                "ratingVotes": 456575,
                "region": "US",
                "runtime": 123,
                "tconst": "tt1979320",
                "title": "Rush",
                "writerNames": ["Peter Morgan"],
                "writers": ["nm0604948"],
                "year": 2013,
            },
        ],
        "directorwriter": [
            {
                "adult": False,
                "directorNames": ["Justin Lin"],
                "directors": ["nm0510912"],
                "genres": ["Action", "Adventure", "Crime"],
                "poster": "https://image.tmdb.org/t/p/w200/wXXYH1VGyVEE2PQS6WvzejZdsou.jpg",
                "rating": 7.3,
                "ratingVotes": 369017,
                "region": "US",
                "runtime": 130,
                "tconst": "tt1596343",
                "title": "Fast Five",
                "writerNames": ["Chris Morgan", "Gary Scott Thompson"],
                "writers": ["nm0604555", "nm0860155"],
                "year": 2011,
            },
            {
                "adult": False,
                "directorNames": ["Justin Lin"],
                "directors": ["nm0510912"],
                "genres": ["Action", "Crime", "Thriller"],
                "poster": "https://image.tmdb.org/t/p/w200/bOFaAXmWWXC3Rbv4u4uM9ZSzRXP.jpg",
                "rating": 5.2,
                "ratingVotes": 104278,
                "region": "US",
                "runtime": 143,
                "tconst": "tt5433138",
                "title": "F9: The Fast Saga",
                "writerNames": [
                    "Daniel Casey",
                    "Justin Lin",
                    "Alfredo Botello",
                    "Gary Scott Thompson",
                ],
                "writers": ["nm0143403", "nm0510912", "nm2073574", "nm0860155"],
                "year": 2021,
            },
        ],
        "genre": [
            {
                "adult": False,
                "directorNames": ["James Wan"],
                "directors": ["nm1490123"],
                "genres": ["Action", "Adventure", "Thriller"],
                "poster": "https://image.tmdb.org/t/p/w200/wurKlC3VKUgcfsn0K51MJYEleS2.jpg",
                "rating": 7.1,
                "ratingVotes": 377187,
                "region": "US",
                "runtime": 137,
                "tconst": "tt2820852",
                "title": "Furious 7",
                "writerNames": ["Chris Morgan", "Gary Scott Thompson"],
                "writers": ["nm0604555", "nm0860155"],
                "year": 2015,
            },
            {
                "adult": False,
                "directorNames": ["Lana Wachowski", "Lilly Wachowski"],
                "directors": ["nm0905154", "nm0905152"],
                "genres": ["Action", "Sci-Fi"],
                "poster": "https://image.tmdb.org/t/p/w200/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
                "rating": 8.7,
                "ratingVotes": 1780724,
                "region": "US",
                "runtime": 136,
                "tconst": "tt0133093",
                "title": "The Matrix",
                "writerNames": ["Lilly Wachowski", "Lana Wachowski"],
                "writers": ["nm0905152", "nm0905154"],
                "year": 1999,
            },
        ],
    }, 200


# Looks up a movie in the database and returns the (parsed) information in a dictionary.
def lookup_movie(tconst):
    # Execute query against local database to get the movie info
    imdb, _ = get_dbs()
    cur = imdb.cursor()
    cur.execute("SELECT * from titles WHERE tconst=?", [tconst])
    rows = cur.fetchall()
    if len(rows) != 1:  # No entry for this movie
        return None

    # Extract result
    (
        tconst,
        title,
        adult,
        year,
        runtime,
        genres,
        region,
        directors,
        writers,
        rating,
        ratingVotes,
        poster,
    ) = rows[-1]

    # Cast adult field from 0/1 to bool
    adult = bool(int(adult))

    # Genres, directors, and writers are comma-delimited strings,
    # so we'll split them into lists
    genres = genres.split(",")
    directors = directors.split(",")
    writers = writers.split(",")

    # Extract actual names of directors/writers via nconsts
    def lookup_name(nconst):
        cur.execute("SELECT * from names WHERE nconst=?", [nconst])
        rows = cur.fetchall()
        if len(rows) < 1:
            return ""
        # Extract and return result
        nconst, name, birthYear, deathYear, profession, titles = rows[-1]
        return name

    director_names = list(map(lookup_name, directors))
    writer_names = list(map(lookup_name, writers))

    # Return parsed dictionary
    return {
        "tconst": tconst,
        "title": title,
        "adult": bool(int(adult)),
        "year": year,
        "runtime": runtime,
        "genres": genres,
        "region": region,
        "directors": directors,
        "directorNames": director_names,
        "writers": writers,
        "writerNames": writer_names,
        "rating": rating,
        "ratingVotes": ratingVotes,
        "poster": poster,
    }


# Returns singleton instances of the IMDB Sqlite3 database and Wikipedia dictionary,
# and stores them on the global application context.
def get_dbs():
    imdb = getattr(g, "_imdb", None)
    if imdb is None:
        imdb = g._imdb = load_imdb()
    wikipedia = getattr(g, "_wikipedia", None)
    if wikipedia is None:
        wikipedia = g._wikipedia = load_wikipedia()

    return imdb, wikipedia


# Loading helpers for IMDB/Wikipedia datasets
load_imdb = lambda: sqlite3.connect(IMDB_DB)
load_wikipedia = lambda: pickle.load(open(WIKIPEDIA_DB, "rb"))


# Automatically close the DB connection on application exit
@app.teardown_appcontext
def close_connection(_):
    db = getattr(g, "_imdb", None)
    if db is not None:
        db.close()
