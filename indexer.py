import os
import json
import math
from bs4 import BeautifulSoup
from token_util import tokenize, compute_token_frequencies
from score_util import compute_tf_idf


DOC_ID = 0

DOC_ID_URL_MAP = {}

OFFLOAD_COUNTER = 0

# posting = (docid, tf, imp)
DOCID = 0
TF = TFIDF = 1
IMP = 2

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
                    token_frequencies = compute_token_frequencies(tokens)
                    important_tokens = get_important_tokens(soup)
                    add_postings(id, token_frequencies, important_tokens, inverted_index)
                    if DOC_ID % 15000 == 0:
                        print(f"Offloading inverted index into p_index{OFFLOAD_COUNTER}.txt")
                        offload_index(inverted_index)
        
    if len(inverted_index) != 0:
        print(f"Offloading inverted index into p_index{OFFLOAD_COUNTER}.txt")
        offload_index(inverted_index)

    with open(os.path.join("Auxilary", "DocID_map.json"), "w") as outfile:
        json.dump(DOC_ID_URL_MAP, outfile)

def assign_docid_to_url(url):
    global DOC_ID
    global DOC_ID_URL_MAP

    id = DOC_ID
    DOC_ID += 1
    DOC_ID_URL_MAP[id] = url
    return id

def get_important_tokens(soup):
    important_tokens = set()
    for tags in soup.find_all(["strong", "b", "h1", "h2", "h3", "title"]):
        text = tags.text.strip()
        tokens = tokenize(text)
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
            outfile.write((token + ":" + str(lst)).replace(" ", "") + "\n")
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
                        outfile.write((key1 + ":" + str(val1)).replace(" ", "") + "\n")
                        line1 = file1.readline()
                        line2 = file2.readline()
        os.remove(os.path.join("Merge", other_file))

def index_the_index(filename):
    index_for_index = {}

    with open(os.path.join("Merge", filename), "r") as file:
        while True:
            pos = file.tell()
            line = file.readline()
            if len(line) == 0:
                break
            else:
                token = line.split(":")[0]
                index_for_index[token] = pos

    with open(os.path.join("Auxilary", "index_for_index.json"), "w") as outfile:
        json.dump(index_for_index, outfile)

def convert_freq_to_norm_tf_idf(source_filename, intermediate_filename, target_filename):
    doc_lengs_for_normalize = {}
    with open(os.path.join("Merge", source_filename), "r") as s_file, open(os.path.join("Merge", intermediate_filename), "w") as i_file:
        line = s_file.readline()
        while len(line) != 0:
            new_posting_list = []
            entry = line.split(":")
            key = entry[0]
            val = eval(entry[1].strip())
            for posting in val:
                tf_idf = compute_tf_idf(posting[TF], None, lambda tf: 1+math.log10(tf), lambda df: 1) #lnc
                if posting[DOCID] not in doc_lengs_for_normalize:
                    doc_lengs_for_normalize[posting[DOCID]] = tf_idf ** 2
                else:
                    doc_lengs_for_normalize[posting[DOCID]] += tf_idf ** 2
                decimal_limited_tf_idf = (tf_idf * 10000) // 1 / 10000
                new_posting = (posting[DOCID], decimal_limited_tf_idf, 1 if posting[IMP] else 0)
                new_posting_list.append(new_posting)
            i_file.write((key + ":" + str(new_posting_list)).replace(" ", "") + "\n")
            line = s_file.readline()
    for docid in doc_lengs_for_normalize:
        doc_lengs_for_normalize[docid] = math.sqrt(doc_lengs_for_normalize[docid])
    with open(os.path.join("Merge", intermediate_filename), "r") as i_file, open(os.path.join("Merge", target_filename), "w") as t_file:
        line = i_file.readline()
        while len(line) != 0:
            new_posting_list = []
            entry = line.split(":")
            key = entry[0]
            val = eval(entry[1].strip())
            for posting in val:
                norm_tf_idf = posting[TFIDF] / doc_lengs_for_normalize[posting[DOCID]]
                decimal_limited_norm_tf_idf = (norm_tf_idf * 10000) // 1 / 10000
                new_posting = (posting[DOCID], decimal_limited_norm_tf_idf, posting[IMP])
                new_posting_list.append(new_posting)
            t_file.write((key + ":" + str(new_posting_list)).replace(" ", "") + "\n")
            line = i_file.readline()
    with open(os.path.join("Auxilary", "doc_lengs_for_normalize.json"), "w") as outfile:
        json.dump(doc_lengs_for_normalize, outfile)

def get_num_docs():
    return len(DOC_ID_URL_MAP)

def get_num_unq_toks(filename):
    num_toks = 0
    with open(os.path.join("Merge", filename), "r") as file:
        while True:
            line = file.readline()
            if len(line) == 0:
                break
            else:
                num_toks += 1
    return num_toks

def get_sz_idx(filename):
    return os.path.getsize(os.path.join("Merge", filename)) / 1024

if __name__ == "__main__":
    #build_index("DEV")
    #merge_partial_indices()
    convert_freq_to_norm_tf_idf("full_index.txt", "intermediate_full_index.txt", "final_full_index.txt")
    index_the_index("final_full_index.txt")
    print(f"Number of documents: {get_num_docs()}")
    print(f"The number of unique tokens: {get_num_unq_toks('final_full_index.txt')}")
    print(f"Size of index in kb: {get_sz_idx('final_full_index.txt')}")
    