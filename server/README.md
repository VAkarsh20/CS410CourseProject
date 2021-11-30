## Server

This folder contains the back-end service used for the Chrome extension. It is a relatively straightforward Flask app that exposes two endpoints:

* `GET /movie?tconst=<some tconst>` returns information about a single movie, including its title, poster, and other metadata.
* `GET /similar?tconst=<some tconst>&by=<some filter>` returns a list of similar movies for a given title, where the optional `by` parameter applies a constraint to the similar movies. `by` can take on the value `directorwriter` or `genre` which constrains the similar movies to be by the same director(s)/writer(s) or the same genre, respectively.

### Setup

Running this server requires two data files: `imdb.db` and `wikipedia.p`. See the [README.md](https://github.com/VAkarsh20/CS410CourseProject/blob/main/database/README.md) from the database folder, which includes download links for these files. Place these files in the same directory as `app.py`, or specify their exact path by changing the constants at the top of `app.py`. Dummy versions of the above endpoints (`/dummy_movie` and `/dummy_similar`) for testing purposes are provided which don't require the database files and return static results.

Once the data files have been acquired, running the server is rather simple, provided Python >=3.6 is installed.

1. (Optional) Setup a virtual environment with `python -m venv venv` and activate it with `source venv/bin/activate`.
2. Install the required dependencies by running `pip install -r requirements.txt`.
3. Start the server by running `FLASK_APP=app flask run`. The server should now be available at `127.0.0.1` on the default Flask port. You can test this by opening up a browser and trying to fetch the movie information for *The Fast and the Furious: Tokyo Drift (2006)*. If Flask started the server on port 5000, you could do this by accessing `http://127.0.0.1:5000/movie?tconst=tt0463985`. You should see the following output:

```json
{
  "adult": false,
  "directors": [
    "nm0510912"
  ],
  "genres": [
    "Action",
    "Crime",
    "Thriller"
  ],
  "rating": 6.0,
  "ratingVotes": 259332,
  "region": "US",
  "runtime": 104,
  "tconst": "tt0463985",
  "title": "The Fast and the Furious: Tokyo Drift",
  "writers": [
    "nm0604555"
  ],
  "year": 2006
}
```