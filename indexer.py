import os
import json
import re
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
from collections import namedtuple


DOC_ID = 0

DOC_ID_URL_MAP = {}

POSTING = namedtuple("POSTING", ["docid", "freq"])

def build_index(root_dir):
    global DOC_ID
    global DOC_ID_URL_MAP 

    inverted_index = {}

    corpus = os.listdir(root_dir)
    for f in corpus:
        file = os.path.join(root_dir, f)
        if os.path.isdir(file):
            pages = os.listdir(file)
            for p in pages:
                print(DOC_ID)
                try:
                    with open(os.path.join(file, p), "r") as json_file:
                        data = json.load(json_file)

                    id = assign_docid_to_url(data["url"])
                    soup = BeautifulSoup(data["content"], "html.parser")
                    tokens = tokenize(soup.get_text())
                    ps = PorterStemmer()
                    tokens = [ps.stem(token) for token in tokens]
                    token_frequencies = compute_token_frequencies(tokens)
                    add_postings(id, token_frequencies, inverted_index)
                except:
                    print("Something wrong with opening file " + p)

    with open("index.json", "w") as outfile:
        json.dump(inverted_index, outfile)

    with open("DocID_map.json", "w") as outfile:
        json.dump(DOC_ID_URL_MAP, outfile)

    print("Number of documents: " + len(DOC_ID_URL_MAP))
    print("The number of unique tokens: " + len(inverted_index))
    print("Size of index in kb:" + os.path.getsize("index.json")/1024)

def add_postings(id, token_frequencies, inverted_index):
    for token in token_frequencies:
        posting = POSTING(id, token_frequencies[token])
        if token not in inverted_index:
            inverted_index[token] = [posting]
        else:
            inverted_index[token].append(posting)

def assign_docid_to_url(url):
    global DOC_ID
    global DOC_ID_URL_MAP

    id = DOC_ID
    DOC_ID += 1
    DOC_ID_URL_MAP[id] = url
    return id

def tokenize(text):
    text = text.lower()
    l = 0
    while l < len(text) and not ("a" <= text[l] <= "z" or "0" <= text[l] <= "9"):
        l += 1
    r = len(text)-1
    while r >= 0 and not ("a" <= text[r] <= "z" or "0" <= text[r] <= "9"):
        r -= 1
    tokens = re.split(r"[^a-z0-9]+", text[l:r+1])
    return tokens

def compute_token_frequencies(tokens):
    token_frequencies = {}
    for token in tokens:
        if token not in token_frequencies:
            token_frequencies[token] = 1
        else:
            token_frequencies[token] += 1
    return token_frequencies

if __name__ == "__main__":
    build_index("DEV")