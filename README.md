# 1. Overview (with Presentation)
This project is a Chrome extension used for retrieving movies simliar to the movie present on the user's tab. When a user searches for a movie on Chrome and opens the extension, movie metadata and similar movies will be presented. 

Detailed README files can be found in each sub-folder describing the specific implementation of all the components of this project. For a high-level overview of its functionality, basic installation instructions, and a demonstration of the Chrome extension being used please refer to this video: https://www.youtube.com/watch?v=_hyaSEG3M44

# 2. Implementation Documenation
## `/database/`
The back-end for this project principally relies on two datasets:

* Metadata about movies (titles, crew, genre, etc) from IMDB and poster URLs from TMDB
* Textual descriptions of movies (reviews, summary, etc) from Wikipedia

The database folder is primarily used for generating these databases. (see [Database Generation](#database-generation)).
### IMDb Database
 To generate the IMDb database, the `gen_imdb_db.py` script must be ran, or the dataset file can be downloaded. The script downloads all the relevant data for every movie in the IMDb database via files provided by IMDb. Then, the data is organized and cleaned, and it is pushed to a local SQLite server. The relevant data pushed for each movie includes the title, release year, runtime, genres, rating, region, crew, and poster. 
### Wikipedia Database
 To generate the Wikipedia database, the `gen_wikipedia_db.py` script must be ran, or the dataset file can be downloaded. The script downloads the Wikipedia page for every movie retrieved in the local IMDb database and pushes the critical response content to a local SPARQL server. 
 
 To retrieve the correct Wikipedia page, the script executes a SPARQL query on a Wikidata endpoint for the corresponding Wikiepdia page link. Here, the IMDb title number is provided as an input. Furthermore, to avoid using the Wikipedia endpoint repeatedly, a version of Wikipedia is hosted on the local machine. This is done by retrieving a ZIM dump of a recent version of Wikipedia, hosting it via Kiwix, and querying it instead.


## `/server/`
The back-end for this project primarily uses two files:
* `app.py`
* `model.py`
### `app.py`
`app.py` is used to host a Flask app for queryable endpoints for the front-end. These endpoints include `/movie` and `/similar`. 

The `/movie` endpoint is used to retrieve all of the data for a given title number. This is done by executing a simple SQL query on the local IMDb database. All of the data is then returned to the front-end.

The `/similar` endpoint is used to retrieve similar movies for a given title number. This is done first by retrieving a list of similarity scores in descending sorted order of other movies provided from `model.py`. Then, the movies are iterated over to retrieve the IMDb data and to be added to a separate list if iterated movie shares the same information to the inputted movie. The compared information currently includes the director/writer or genre(s). Finally, these lists are returned to the front-end, each up to a limit if provided.

### `model.py`
`model.py` is used to calculate and store the similarity scores between each movie in the database. To achieve this, first, the Wikipedia entires must be preprocessed and cleaned. This involves removing unwanted characters, like non-ASCII, citations, and newlines; and tokenizing the entry, while also removing punctuation and stop words. Then, a cosine similarity matrix is built over the entire corpus using Scikit-learn. Finally, similarity scores for a given movie can be retrieved, and a sorted list of the other movies' title numbers and similarity scores are provided.

## `/chrome-extension/`
unknown

# 3. Usage Documentation
## Database Generation


The scripts in the project are meant to assist in the creation of two datasets:

* [imdb.db (Sqlite3 DB, ~1 GB)](https://drive.google.com/file/d/1jlYawRw3HDthGsxZNQYrWliYEGztTVCQ/view?usp=sharing)
* [wikipedia.p (Python dictionary, ~15 MB)](https://drive.google.com/file/d/1LDV9-5GKlacbMOxiZ613_69EL4G7aQXS/view?usp=sharing)

These database files take a non-trivial amount of time to generate. As such, they have been uploaded elsewhere and should be checked out directly to be used in the application. The scripts located in the repoository have only been uploaded for reproducability. See the [Database README](https://github.com/VAkarsh20/CS410CourseProject/blob/main/database/README.md) for more information.

## Installation
unknown
## Usage
unknown

# 4. Team Member Contributions
The development team consisted of 5 members, so it was expected that 100 hours of work was done for the project. The each team member did roughly 20 hours of work and their contributions were as follows:
* Akarsh Vankayalapati (Captain): Akarsh was the acting project manager of the group and set weekly checkins with the group to see how the project was going and what was needed to get past and hurdles hindering productivity. Along with this, Akarsh designed the project at a very high level, delegated tasks out to other members, and helped with the implementation of the front-end.
* John Armgardt: John was in charge of making the API calls to IMDb and Wikipedia and scraping the data to be put into the database.
* Ian Goodwin: Ian was in charge of the front-end implementation of the project that took end points from the back-end and displayed them with the chrome extension.
* Aditya Mansharamani: Adithya was in charge of the Backend implementation of the project as he helped connect the parts John and Spencer were working on to develop the model overall. 
* Spencer Sullivan-Hayes: Spencer was helped create the Vector Space for the model with John. Also, Spencer was in charge of the presentation portion of the project.
