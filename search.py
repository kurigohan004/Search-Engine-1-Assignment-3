import os
import json
import time
from token_util import tokenize

# posting = (docid, tf, imp)
DOCID = 0
TF = 1
IMP = 2

def intersect(a, b):
    res = []
    i = 0
    j = 0
    while i < len(a) and j < len(b):
        if a[i][DOCID] < b[j][DOCID]:
            i += 1
        elif a[i][DOCID] > b[j][DOCID]:
            j += 1
        else:
            if type(a[i][TF]) == list:
                a[i][TF].append(b[j][TF])
                a[i][IMP].append(b[j][IMP])
                res.append(a[i])
            else:
                res.append((a[i][DOCID], [a[i][TF], b[j][TF]], [a[i][IMP], b[j][IMP]]))
            i += 1
            j += 1
    return res

def get_intersection(all_query_postings):
    all_query_postings = sorted(all_query_postings, key = lambda x: len(x[1]))
    sorted_terms = [x[DOCID] for x in all_query_postings]
    curr_intersection = intersect(all_query_postings[0][1], all_query_postings[1][1])
    for i in range(2, len(all_query_postings)):
        curr_intersection = intersect(curr_intersection, all_query_postings[i][1])
    return (sorted_terms, curr_intersection)

def serve_query(query_tokens, index_file, index_for_index):
    all_query_postings = []
    for token in query_tokens:
        index_file.seek(index_for_index[token])
        line = index_file.readline().strip()
        term, postings = line.split(":")
        postings = eval(postings)
        all_query_postings.append((term, postings))
    if len(all_query_postings) == 1:
        return [x[DOCID] for x in all_query_postings[0][1]]
    else:
        sorted_terms, intersection = get_intersection(all_query_postings)
        # do more
        return [x[DOCID] for x in intersection]

def print_top_5(doc_ids, doc_id_url_map):
    for i, doc_id in enumerate(doc_ids[:5]):
        url = doc_id_url_map[str(doc_id)]
        print(f"{i+1}. {url}")

if __name__ == "__main__":
    with open(os.path.join("Auxilary", "DocID_map.json"), "r") as file:
        doc_id_url_map = json.load(file)
    with open(os.path.join("Auxilary", "index_for_index.json"), "r") as file:
        index_for_index = json.load(file)
    with open(os.path.join("Merge", "full_index.txt"), "r") as file:
        while True:
            start_time = time.time()
            query = input("Enter a query: ")
            if len(query) != 0:
                query_tokens = tokenize(query)
                doc_ids = serve_query(query_tokens, file, index_for_index)
                print_top_5(doc_ids, doc_id_url_map)
            else:
                break
            end_time = time.time()
            resp_time = (end_time-start_time) / 1000
            print(f"Response time to query was {resp_time} ms.")