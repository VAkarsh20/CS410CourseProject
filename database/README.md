## Database generation

The back-end for this project principally relies on two datasets:

* Metadata about movies (titles, crew, genre, etc) from IMDB
* Textual descriptions of movies (reviews, summary, etc) from Wikipedia

The scripts in this folder are meant to assist in the creation of two database files:

* imdb.db
* wikipedia.db

**Note: These database files are rather large, and take a non-trivial amount of time to generate! These files have been commited to Git LFS and should be checked out directly to be used in the application. The scripts located in this repo have only been uploaded for reproducability. See the [Downloads](#downloads) section for more information.**
  
Both database files are indexed by IMDB "title numbers" (also known as *tconst*s). These identifiers generally take the form of `tt<some number>`. For example, the IMDB title number for the movie *The Incredible HulK (2008)* is `tt0800080`. These identifiers are used for two reasons:

* All of IMDB's publicly available datasets are keyed by *tconst*.
* Wikidata allows us to query the corresponding Wikipedia page for a movie using its tconst.

### `imdb.db`

`imdb.db` is a Sqlite3 database containing two tables. The first table, `titles`, contains metadata about the movies found in IMDB: 

```sql
CREATE TABLE "titles" (
  "tconst" TEXT,
  "title" TEXT,
  "adult" TEXT,
  "year" INTEGER,
  "runtime" INTEGER,
  "genres" TEXT,
  "region" TEXT,
  "directors" TEXT,
  "writers" TEXT,
  "rating" REAL,
  "ratingVotes" INTEGER
);
```

Notice that each movie has a "directors" and "writers" field. These fields contain comma-delimited lists of IMDB name identifiers, or *nconst*s. These directors and writers can be looked up in the `names` table:

```sql
CREATE TABLE IF NOT EXISTS "names" (
  "nconst" TEXT,
  "name" TEXT,
  "birthYear" TEXT,
  "deathYear" TEXT,
  "profession" TEXT,
  "titles" TEXT
);
```

Use the python script `gen_imdb_db.py` to generate `imdb.py`. Python version >= 3.6 is required. **Warning: On my machine, this script consumed at peak about 8 GB of memory. It also downloads a decent amount of data. The resulting database file is about 1 GB.**

1. (Optional) Setup a virtual environment with `python -m venv imdb_venv`, and load it with `source imdb_venv/bin/activate`.
2. Install the required Python dependencies with `pip install -r imdb_requirements.txt`.
3. Run the script with `python gen_imdb_db.py`. The script will download the latest datasets from IMDB's website, load them into memory, extract and merge the relevant metadata, and export the data into a single Sqlite3 database called `imdb.db`. The script will also perform a single test query against the database and print the results as a quick sanity check.


## Downloads