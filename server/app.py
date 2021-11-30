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
    return "", 200


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


# Returns singleton instances of the IMDB Sqlite3 database and Wikipedia dictionary
def get_dbs():
    imdb = getattr(g, "_imdb", None)
    if imdb is None:
        imdb = g._imdb = sqlite3.connect(IMDB_DB)
    wikipedia = getattr(g, "_wikipedia", None)
    if wikipedia is None:
        with open(WIKIPEDIA_DB, "rb") as f:
            wikipedia = g._wikipedia = pickle.load(f)

    return imdb, wikipedia


# Automatically close the DB connection on application exit
@app.teardown_appcontext
def close_connection(_):
    db = getattr(g, "_imdb", None)
    if db is not None:
        db.close()
