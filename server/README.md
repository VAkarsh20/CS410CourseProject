## Server

This folder contains the back-end service used for the Chrome extension. It is a relatively straightforward Flask app that exposes two endpoints:

* `GET /movie?tconst=<some tconst>` returns information about a single movie, including its title, poster, and other metadata.
* `GET /similar?tconst=<some tconst>` returns a set of lists of similar movies for a given title. The set contains a list of similar movies in general, a list of similar movies by the same director/writer, and a list of similar movies in the same genre.

### Setup

Running this server requires two data files: `imdb.db` and `wikipedia.p`. See the [README.md](https://github.com/VAkarsh20/CS410CourseProject/blob/main/database/README.md) from the database folder, which includes download links for these files near the bottom. Place these files in the same directory as `app.py`, or specify their exact path by changing the constants at the top of `app.py`. Dummy versions of the above endpoints (`/dummy_movie` and `/dummy_similar`) for testing purposes are provided which don't require the database files and return fixed results. These endpoints have the same schema as their real counterparts.

Once the data files have been acquired, running the server is rather simple, provided Python >=3.6 is installed.

1. (Optional) Setup a virtual environment with `python -m venv venv` and activate it with `source venv/bin/activate`.
2. Install the required dependencies by running `pip install -r requirements.txt`.
3. Start the server by running `python app.py`. This may take up to a minute the first time the server is started, since the similarity model has to be built from scratch. The server should then be available at `127.0.0.1` on the default Flask port. You can test this by opening up a browser and trying to fetch the movie information for *The Fast and the Furious: Tokyo Drift (2006)*. If Flask started the server on port 5000, you could do this by accessing `http://127.0.0.1:5000/movie?tconst=tt0463985`. You should see the following output:

```json
{
  "adult": false,
  "directorNames": [
    "Justin Lin"
  ],
  "directors": [
    "nm0510912"
  ],
  "genres": [
    "Action",
    "Crime",
    "Thriller"
  ],
  "poster": "https://image.tmdb.org/t/p/w200/cm2ffqb3XovzA5ZSzyN3jnn8qv0.jpg",
  "rating": 6.0,
  "ratingVotes": 259332,
  "region": "US",
  "runtime": 104,
  "tconst": "tt0463985",
  "title": "The Fast and the Furious: Tokyo Drift",
  "writerNames": [
    "Chris Morgan"
  ],
  "writers": [
    "nm0604555"
  ],
  "year": 2006
}
```

### Schema - `/movie`

A `movie` object has the following JSON schema:
```json
{
  "adult": bool,
  "directorNames": Array[string],
  "directors": Array[nconst (string)],
  "genres": Array[string],
  "poster": URL (string),
  "rating": float,
  "ratingVotes": int,
  "region": string,
  "runtime": int,
  "tconst": tconst (string),
  "title": string,
  "writerNames": Array[string],
  "writers": Array[nconst (string)],
  "year": int
}
```

`GET /movie?tconst=<some tconst>` simply returns a single movie.

### Schema - `/similar`

`GET /similar?tconst=<some tconst>?limit=<some num>` simply returns a set of lists of similar movies with the following schema.

```json
{
  "all": Array[movie], // similar movies (in general)
  "directorwriter": Array[movie], // similar movies by the same director/writer
  "genre": Array[movie] // similar movies in the same genre
}
```

The **optional** `limit` parameter can be used to limit how many movies are returned for _each_ category. By default, all movies that had a similarity score greater than `0` can be returned.


### How it works

In order to rank movies based on the similarity between their Wikipedia descriptions, the server constructs a similarity model. Before the model can be constructed, we first need to pre-process the raw dataset consisting of the "Critical response" section of the Wikipedia page for each movie. Without pre-processing the data, not only would the model's size blow up, it would be less useful as the quality of the dataset would lend itself to providing good similarity measures between movies. The following pre-processing steps were applied using `nltk`:

- Removing unnecessary whitespace characters, non-ASCII characters, and citations
- Removing punctuation
- Removing stopwords ("the", "is", etc)
- Lowercasing
- Stemming

Once the data is pre-processed, the entire corpus of text is transformed to counts using `scikit-learn`'s TF-IDF vectorizer. Then, the cosine similarity metric is calculated for each pair of movies, ultimately resulting in a (rather large) lookup table `M` where `M[i][j]` is the cosine similarity between the movies with index `i` and `j`. 

Translating the lookup table into movie recommendations is rather straightforward: we simply look at a single row `i` of `M` and extract the (`j`, score) pairs for each *other* movie `j` in the dataset. We can then sort these scores in reverse order, remove any movies with 0-score, and we have our final list of similar movies ordered from most-similar to least-similar. These results can further be decomposed into similar movies by the same director or of the same genre.