from flask import Flask, request, g
import sqlite3, pickle

# Change these if you are using different locations for the data files!
IMDB_DB = "imdb.db"
WIKIPEDIA_DB = "wikipedia.p"


app = Flask("app")


@app.route("/movie")
def get_movie():
    # Invalid request
    if "tconst" not in request.args:
        return "You need to include a tconst!", 400

    # Get movie identifier
    tconst = request.args["tconst"]

    # Execute query against local database to get the movie info
    imdb, _ = get_dbs()
    cur = imdb.cursor()
    cur.execute("SELECT * from titles WHERE tconst=?", [tconst])
    rows = cur.fetchall()
    if len(rows) != 1:  # No entry for this movie
        return "No IMDB entry for this tconst (does it even exist?)", 404

    # Otherwise, parse result
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

    # cast to bool
    adult = bool(int(adult))
    # split lists
    genres = genres.split(",")
    directors = directors.split(",")
    writers = writers.split(",")

    # extract actual names of directors/writers via nconsts
    director_names = []
    for director in directors:
        cur.execute("SELECT * from names WHERE nconst=?", [director])
        rows = cur.fetchall()
        # print(rows)

    return {
        "tconst": tconst,
        "title": title,
        "adult": bool(int(adult)),
        "year": year,
        "runtime": runtime,
        "genres": genres,
        "region": region,
        "directors": directors,
        "writers": writers,
        "rating": rating,
        "ratingVotes": ratingVotes,
    }


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


# Dummy endpoints for testing
@app.route("/dummy_movie")
def get_dummy_movie():
    return ""


@app.route("/dummy_similar")
def get_dummy_similar():
    return ""


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


# Automatically close the DB connection
@app.teardown_appcontext
def close_connection(_):
    db = getattr(g, "_imdb", None)
    if db is not None:
        db.close()
