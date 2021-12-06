import os, tqdm, pickle, re, string, itertools
import numpy as np
from multiprocessing import Pool, cpu_count
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from bidict import bidict

# File to store pickled model resources in
MODEL_FILE = "model_res.p"

# Global variable to store model
_model = None

# Returns the a list of [(tconst, similarity_score)]
# in descending sorted order of similarity score
def get_movie_similarity_scores(tconst):
    global _model
    if _model is None:
        return None

    tconst_map, similarity_matrix, wikipedia = _model


# Initializes the similarity model into global memory
def init_model(wikipedia):
    global _model
    _model = _build_similarity_model(wikipedia)


# Builds an n x n matrix M and corresponding index->tconst list L
# M[i][j] is the cosine similarity between the tconsts L[i] and L[j]
def _build_similarity_model(wikipedia):
    # Load the preprocessed Wikipedia dataset from file if we have it
    if os.path.exists(MODEL_FILE):
        wikipedia = pickle.load(open(MODEL_FILE, "rb"))
    # Otherwise, we need to make it ourselves
    else:
        wikipedia = _preprocess_wikipedia(wikipedia)
        # Dump post-processed Wikipedia dataset to file
        with open(MODEL_FILE, "wb") as f:
            pickle.dump(wikipedia, f)

    # Extract tconsts/entries to separate lists
    tconsts, entries = zip(*wikipedia.entries())
    tconsts, entries = list(tconsts), list(entries)

    # Build cosine similarity matrix M using the entire corpus
    vectorizer = TfidfVectorizer()
    entries_vectorized = vectorizer.fit_transform(entries)
    similarity_matrix = cosine_similarity(entries_vectorized, entries_vectorized)

    # Form index->tconst list L
    tconst_map = bidict({tconst: i for tconst, i in zip(tconsts, range(len(tconsts)))})

    return tconst_map, similarity_matrix, wikipedia


# Preprocess the entire Wikipedia dataset in parallel
def _preprocess_wikipedia(wikipedia):
    # Parallel map the entry parser to generate a new, cleaned dataset
    pool = Pool(processes=cpu_count())
    wikipedia = {
        tconst: entry
        for (tconst, entry) in pool.map(_preprocess_wikipedia_entry, wikipedia.items())
    }
    pool.close()

    return wikipedia


# Preprocess the contents of a single Wikipedia entry
def _preprocess_wikipedia_entry(item):
    tconst, entry = item

    # Replace newlines with spaces
    entry = entry.replace("\n", " ")
    # Replace citations with spaces
    entry = re.sub("\[[0-9]+\]", " ", entry)
    # Replace non-ASCII characters with nothing
    entry = re.sub(r"[^\x00-\x7F]+", "", entry)
    # Strip entry
    entry = entry.strip()

    # Tokenize and remove punctuation + stop words
    stopwords_set = set(stopwords.words("english"))
    entry = word_tokenize(entry)
    entry = list(
        filter(
            lambda token: "'" not in token
            and '"' not in token
            and "`" not in token
            and "." not in token
            and token not in string.punctuation
            and token not in stopwords_set,
            entry,
        )
    )

    # Lower case
    entry = [word.lower() for word in entry]

    # Stem
    # stemmer = PorterStemmer()
    # entry = [stemmer.stem(word) for word in entry]

    # Rejoin entry
    entry = " ".join(entry)

    return tconst, entry
