import os
import json
from bs4 import BeautifulSoup
import re

DOC_ID = 0

DOC_ID_URL_MAP = {}

def build_index(root_dir):
    global DOC_ID

    corpus = os.listdir(root_dir)
    for f in corpus:
        file = os.path.join(root_dir, f)
        if os.path.isdir(file):
            pages = os.listdir(file)
            for p in pages:
                
                json_file = open(os.path.join(file, p), "r")
                data = json.load(json_file)
                json_file.close()

                id = assign_docid_to_url(data["url"])
                soup = BeautifulSoup(data["content"], "html.parser")
                tokens = tokenize(soup.get_text())
                token_frequency = compute_token_frequencies(tokens)

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