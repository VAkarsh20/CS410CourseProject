from flask import Flask, request, g
from model import init_model, get_movie_similarity_scores
from dummy import dummy_movie, dummy_similar
import sqlite3, pickle, time


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
    if "tconst" not in request.args:
        return "Invalid request!", 400

    # Parse limit, if provided
    limit = None
    if "limit" in request.args:
        try:
            limit = int(request.args["limit"])
        except:
            return "Invalid request!", 400

    # Extract title ID
    tconst = request.args["tconst"]

    # Lookup this movie
    movie = lookup_movie(tconst)

    # Get [(tconst, similarity score)] list from model
    similarity_scores = get_movie_similarity_scores(tconst)

    # Remap tconsts --> movie info
    similar_movies_all = list(map(lambda e: lookup_movie(e[0]), similarity_scores))
    similar_movies_directorwriter = []
    similar_movies_genre = []

    # Build similar movie list for same director/writer and genre
    for similar_movie in similar_movies_all:
        if any(x in movie["directors"] for x in similar_movie["directors"]) or any(
            x in movie["writers"] for x in similar_movie["writers"]
        ):
            similar_movies_directorwriter.append(similar_movie)

        if any(x in movie["genres"] for x in similar_movie["genres"]):
            similar_movies_genre.append(similar_movie)

    return {
        "all": similar_movies_all[:limit],
        "directorwriter": similar_movies_directorwriter[:limit],
        "genre": similar_movies_genre[:limit],
    }


# Dummy endpoint for /movie which doesn't require a database
@app.route("/dummy_movie")
def get_dummy_movie():
    return dummy_movie


# Dummy endpoint for /similar which doesn't require a database
@app.route("/dummy_similar")
def get_dummy_similar():
    return dummy_similar


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


if __name__ == "__main__":
    # Initialize the similarity model, then start the server
    with app.app_context():
        start = time.time()
        print("Initializing similarity model...", end=" ", flush=True)
        _, wikipedia = get_dbs()
        init_model(wikipedia)
        print(f"Done [{(time.time() - start):.1f}s]")

    app.run()
