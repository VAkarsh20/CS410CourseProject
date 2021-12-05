import os, tqdm, pickle, re, string, itertools
import numpy as np
from multiprocessing import Pool, cpu_count
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_PATH = "model.p"

# Loads or builds an n x n matrix M
# M[tconst1][tconst2] represents the similarity between the movies
# tconst1 and tconst2.
def load_or_build_model(imdb, wikipedia, pool):

    # If a previous model has already been build and exists, load it
    # Otherwise, we need to construct the model.
    if os.path.exists(MODEL_PATH):
        return pickle.load(open(MODEL_PATH, "rb"))

    # Tokenize each wikipedia entry
    wikipedia = {
        tconst: entry
        for (tconst, entry) in pool.map(tokenize_wikipedia_entry, wikipedia.items())
    }

    # Build cosine similarity matrix using the entire corpus
    keys, values = list(wikipedia.keys()), list(wikipedia.values())
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(values)
    sim = cosine_similarity(X, X)

    # Return ordered key list and similarity matrix
    return keys, sim


# Tokenize the contents of the Wikipedia dataset
def tokenize_wikipedia_entry(item):
    key, entry = item

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

    return key, entry


# This file should be imported by the server, but here's some test driver code.
if __name__ == "__main__":
    from app import load_imdb, load_wikipedia

    imdb = load_imdb()
    wikipedia = load_wikipedia()

    with Pool(processes=cpu_count()) as pool:
        wikipedia = load_or_build_model(imdb, wikipedia, pool)
