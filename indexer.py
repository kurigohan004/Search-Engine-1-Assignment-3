import os
import json
import re
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer


DOC_ID = 0

DOC_ID_URL_MAP = {}

OFFLOAD_COUNTER = 0

def build_index(root_dir):
    global DOC_ID
    global DOC_ID_URL_MAP
    global OFFLOAD_COUNTER

    inverted_index = {}

    corpus = os.listdir(root_dir)
    for f in corpus:
        file = os.path.join(root_dir, f)
        if os.path.isdir(file):
            pages = os.listdir(file)
            for p in pages:
                print(DOC_ID)
                with open(os.path.join(file, p), "r") as json_file:
                    data = json.load(json_file)
                    id = assign_docid_to_url(data["url"])
                    soup = BeautifulSoup(data["content"], "html.parser")
                    tokens = tokenize(soup.get_text())
                    ps = PorterStemmer()
                    tokens = [ps.stem(token) for token in tokens]
                    token_frequencies = compute_token_frequencies(tokens)
                    important_tokens = get_important_tokens(soup)
                    add_postings(id, token_frequencies, important_tokens, inverted_index)
                    if DOC_ID % 10000 == 0:
                        print(f"Offloading inverted index into p_index{OFFLOAD_COUNTER}.txt")
                        offload_index(inverted_index)
        
    if len(inverted_index) != 0:
        print(f"Offloading inverted index into p_index{OFFLOAD_COUNTER}.txt")
        offload_index(inverted_index)

    with open("DocID_map.json", "w") as outfile:
        json.dump(DOC_ID_URL_MAP, outfile)

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
    return [token for token in tokens if token != ""]

def compute_token_frequencies(tokens):
    token_frequencies = {}
    for token in tokens:
        if token not in token_frequencies:
            token_frequencies[token] = 1
        else:
            token_frequencies[token] += 1
    return token_frequencies

def get_important_tokens(soup):
    important_tokens = set()
    for tags in soup.find_all(["b", "h1", "h2", "h3", "title"]):
        text = tags.text.strip()
        ps = PorterStemmer()
        tokens = tokenize(text)
        tokens = [ps.stem(token) for token in tokens]
        important_tokens.update(tokens)
    return important_tokens

def add_postings(id, token_frequencies, important_tokens, inverted_index):
    for token in token_frequencies:
        posting = (id, token_frequencies[token], token in important_tokens)
        if token not in inverted_index:
            inverted_index[token] = [posting]
        else:
            inverted_index[token].append(posting)

def offload_index(inverted_index):
    global OFFLOAD_COUNTER
    address = os.path.join("Partial", f"p_index{OFFLOAD_COUNTER}.txt")
    with open(address, "w") as outfile:
        for token, lst in sorted(inverted_index.items()):
            outfile.write(token + ":" + str(lst) + "\n")
        inverted_index.clear()
        OFFLOAD_COUNTER += 1

def merge_partial_indices():
    partial_indices = os.listdir("Partial")
    for i, f in enumerate(sorted(partial_indices)):
        merge_file = f"m_index{i}.txt" if i < len(partial_indices)-1 else "full_index.txt"
        other_file = f"m_index{i-1}.txt" if i > 0 else "dummy.txt"
        with open(os.path.join("Partial", f), "r") as file1, open(os.path.join("Merge", other_file), "r") as file2 , open(os.path.join("Merge", merge_file), "w") as outfile:
            line1 = file1.readline()
            line2 = file2.readline()
            while True:
                if len(line1) == 0 and len(line2) == 0:
                    break
                elif len(line1) == 0:
                    while len(line2) != 0:
                        outfile.write(line2)
                        line2 = file2.readline()
                    break
                elif len(line2) == 0:
                    while len(line1) != 0:
                        outfile.write(line1)
                        line1 = file1.readline()
                    break
                else:
                    entry1 = line1.split(":")
                    entry2 = line2.split(":")
                    key1 = entry1[0]
                    val1 = eval(entry1[1].strip())
                    key2 = entry2[0]
                    val2 = eval(entry2[1].strip())
                    if key1 < key2:
                        outfile.write(line1)
                        line1 = file1.readline()
                    elif key1 > key2:
                        outfile.write(line2)
                        line2 = file2.readline()
                    else:
                        val1.extend(val2)
                        outfile.write(key1 + ":" + str(val1) + "\n")
                        line1 = file1.readline()
                        line2 = file2.readline()

def get_num_docs():
    return len(DOC_ID_URL_MAP)

def get_num_unq_toks():
    num_toks = 0
    with open(os.path.join("Merge", "full_index.txt")) as file:
        while True:
            line = file.readline()
            if len(line) == 0:
                break
            else:
                num_toks += 1
    return num_toks

def get_sz_idx():
    return os.path.getsize(os.path.join("Merge", "full_index.txt")) / 1024

if __name__ == "__main__":
    build_index("DEV")
    merge_partial_indices()
    print(f"Number of documents: {get_num_docs()}")
    print(f"The number of unique tokens: {get_num_unq_toks()}")
    print(f"Size of index in kb: {get_sz_idx()}")