## Database generation

The back-end for this project principally relies on two datasets:

* Metadata about movies (titles, crew, genre, etc) from IMDB and poster URLs from TMDB
* Textual descriptions of movies (reviews, summary, etc) from Wikipedia

The scripts in this folder are meant to assist in the creation of two datasets:

* imdb.db (Sqlite3 DB, ~1 GB)
* wikipedia.p (Python dicctionary, ~15 MB)

**Note: These database files take a non-trivial amount of time to generate! These files have been uploaded elsewhere and should be checked out directly to be used in the application. The scripts located in this repo have only been uploaded for reproducability. See the [Downloads](#downloads) section for more information.**
  
Both data files are indexed by IMDB "title numbers" (also known as *tconst*s). These identifiers generally take the form of `tt<some number>`. For example, the IMDB title number for the movie *The Incredible HulK (2008)* is `tt0800080`. These identifiers are used for two reasons:

* All of IMDB's publicly available datasets are keyed by *tconst*.
* Wikidata allows us to query the corresponding Wikipedia page for a movie using its tconst.

### `imdb.db`

`imdb.db` is a Sqlite3 database containing two tables. The first table, `titles`, contains metadata about the movies found in IMDB. Poster URLs were also pulled from TMDB.

```sql
CREATE TABLE IF NOT EXISTS "titles" (
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
  "ratingVotes" INTEGER,
  "poster" TEXT
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

1. (Optional) Setup a virtual environment with `python -m venv venv`, and load it with `source venv/bin/activate`.
2. (Optional) Get an API key from [TMDB](https://www.themoviedb.org/settings/api) to download poster URLs for movies.
3. Install the required Python dependencies with `pip install -r requirements.txt`.
4. Run the script with `python gen_imdb_db.py`. The script will ask if you want to download poster URLs, and ask for an API key if you say yes. The script will download the latest datasets from IMDB's website, load them into memory, extract and merge the relevant metadata, and export the data (including poster URLs if specified) into a single Sqlite3 database called `imdb.db`. The script will also perform a single test query against the database and print the results as a quick sanity check.

### `wikipedia.p`

**Note: We will need the IMDB database generated in the previous step to make this database.**

Generating this dataset is a bit trickier, for two reasons.

1. There is no obvious method for locating the corresponding Wikipedia page for a given IMDB entry.
2. We don't want to spam Wikipedia's services with requests to perform large amounts of crude web scraping. Wikipedia is a free service and it would be very rude to hammer their servers for a school project.

Luckily, some [digging](https://www.bobdc.com/blog/imdb2wp/) led to this key fact: [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page) maintains entries for almost every _entity_ across the Wikimedia projects, including Wikipedia. What's even more important is that they have the ability to associate these entities with external (i.e. not specific to Wikipedia/Wikimedia) sources... including IMDB! Wikidata provides a nice SPARQL endpoint for querying their database, and we can query the corresponding Wikipedia page (if one exists) for an IMDB entry like so:

```
SELECT ?wppage WHERE {{
            ?subject wdt:P345 '<some IMDB ID>' . 
            ?wppage schema:about ?subject .
            FILTER(contains(str(?wppage),'//en.wikipedia'))
```

I tried to initially host a local version of Wikidata so we wouldn't have to hammer their servers, but the raw RDF export of Wikidata is about ~100 GB and had download speed capped to about 2 MB/s. They do make it awfully easy to host a local version of their SPARQL server, but due to the slow download speed we will just hit their SPARQL endpoint to fetch the Wikipedia page links. Luckily it seems like the endpoint does throttle you to just a few (maybe one?) parallel queries per IP, but has no limit on the number of sequential queries. 

Now that we can match IMDB entries to Wikipedia pages, the next challenge is somehow getting access to the Wikipedia page and extracting some sections of interest. Here, we *can* avoid hitting the Wikipedia endpoint repeatedly, by hosting our own local version of Wikipedia! There are a few ways to do this, but I found the easiest was hosting a static version of Wikipedia provided in ZIM format using a tool called [Kiwix](https://www.kiwix.org/en/). Bonus: Wikipedia provides ZIM downloads of subcatgories of the website, including just movies. 

We can download ZIM dumps of Wikipedia from [here](https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/). The script in `wikipedia_kiwix/data/download.sh` will download the movie ZIM dump used in this project. Make sure the ZIM file is in the `wikipedia_kiwix/data` folder, and then start the Kiwix docker container from the `wikipedia_kiwix` folder by running `docker-compose up` (you will obviously need to have Docker installed).

The local copy of Wikipedia should now be available at [localhost:8888](localhost:8888). We will need to extract the root URL of the Wikipedia instance, which is related to the ZIM file used for serving it. Navigate it to an arbitrary page. The URL will look like the following - the root path is everything before (and including) the `A/`. So if a page has the following path:

`http://localhost:8888/wikipedia_en_movies_nopic_2021-10/A/The_Incredible_Hulk_(film)`

The root path is `http://localhost:8888/wikipedia_en_movies_nopic_2021-10/A/`. This root path effectively replaces `https://en.wikipedia.org/wiki/` for the URLs we're going to get back from Wikidata.

Now, we can open up `gen_wikipedia_db.py` and replace `LOCAL_WIKIPEDIA_ROOT` at the top with the root path we just found. Make sure the script is in the same folder as `imdb.db`, setup the virtual environment/dependencies as described in the `imdb.db` section, and then go ahead and run the script: `python gen_wikipedia_db.py`.

This will take a while (~6 hours) due to the large amount of queries to Wikidata and our local Wikipedia instance. The end result should be `wikipedia.p`, which is a [pickled](https://docs.python.org/3/library/pickle.html) Python dictionary with string keys (*tconst*s) and string values (the Wikipedia critical reviews/response section from that title's page). This dataset can be loaded directly into memory since it's rather small (and will probably need to be to do any meaningful document ranking!)

## Downloads

* [imdb.db](https://drive.google.com/file/d/1jlYawRw3HDthGsxZNQYrWliYEGztTVCQ/view?usp=sharing)
* [wikipedia.p](https://drive.google.com/file/d/1LDV9-5GKlacbMOxiZ613_69EL4G7aQXS/view?usp=sharing)

## Credits

* [IMDB](https://www.imdb.com)
* [Wikipedia](https://www.wikipedia.org), [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page)
* [The Movie Database (TMDB)](https://www.themoviedb.org)