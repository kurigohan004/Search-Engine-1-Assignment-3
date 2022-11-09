import re
from nltk.stem import PorterStemmer


def tokenize(text):
    text = text.lower()
    l = 0
    while l < len(text) and not ("a" <= text[l] <= "z" or "0" <= text[l] <= "9"):
        l += 1
    r = len(text)-1
    while r >= 0 and not ("a" <= text[r] <= "z" or "0" <= text[r] <= "9"):
        r -= 1
    tokens = re.split(r"[^a-z0-9]+", text[l:r+1])
    ps = PorterStemmer()
    tokens = [ps.stem(token) for token in tokens]
    return [token for token in tokens if token != ""]

def compute_token_frequencies(tokens):
    token_frequencies = {}
    for token in tokens:
        if token not in token_frequencies:
            token_frequencies[token] = 1
        else:
            token_frequencies[token] += 1
    return token_frequencies