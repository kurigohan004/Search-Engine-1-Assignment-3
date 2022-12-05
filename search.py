import os
import json
import time
import math
import heapq
import ast
from token_util import tokenize, compute_token_frequencies
from score_util import compute_tf_idf

# posting = (docid, tf, imp)
DOCID = 0
SCORE = 1
IMP = 2

N = 55393 #number of docs

"""
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
"""
def convert_str_to_postings(postings_str):
    postings = []
    curr_posting = [0,0,0]
    curr_posting_idx = 0
    curr_val = ""
    for ch in postings_str:
        if ch == "[" or ch == "]":
            pass
        elif ch == "(":
            curr_posting = [0,0,0]
            curr_posting_idx = 0
            curr_val = ""
        elif ch == ",":
            if curr_posting_idx == DOCID:
                curr_posting[curr_posting_idx] = int(curr_val)
            elif curr_posting_idx == SCORE:
                curr_posting[curr_posting_idx] = float(curr_val)
            curr_posting_idx += 1
            curr_val = ""
        elif ch == ")":
            curr_posting[curr_posting_idx] = int(curr_val)
            postings.append(tuple(curr_posting))
        else:
            curr_val += ch
    return postings

def convert_str_to_postings2(postings_str):
    postings_str = postings_str[2:len(postings_str)-2]
    postings = postings_str.split("),(")
    for i in range(len(postings)):
        temp = postings[i].split(",")
        postings[i] = (int(temp[DOCID]), float(temp[SCORE]), int(temp[IMP]))
    return postings

def get_top_5_queries_from_docs_and_scores(docs_and_scores):
    # get top 5 documents using heap
    SCORE = 0 #makes indexing cleaner
    heap = [] #initialize empty heapq
    for docid, score in docs_and_scores.items():
        if len(heap)<5: # if there are not 5 element in heapq, just add them 
            heapq.heappush(heap, (score, docid))
        else:
            # if current docid score is larger, then remove lowest score and add this one 
            if score > heap[0][SCORE]:
                heapq.heappushpop(heap, (score, docid)) # faster than doing separate push and then pop operations
    return heap

def get_docs_and_scores(all_query_postings, query_norm_tf_idfs):
    # compute score for any document that has at least one of the query tokens 
    docs_and_scores = {}
    for i in range(len(all_query_postings)):
        for posting in all_query_postings[i][1]:
            imp_factor = 1 if posting[IMP] else (1/2) # give important words twice the weight
            if posting[DOCID] not in docs_and_scores:
                docs_and_scores[posting[DOCID]] = posting[SCORE] * query_norm_tf_idfs[i] * imp_factor
            else:
                docs_and_scores[posting[DOCID]] += posting[SCORE] * query_norm_tf_idfs[i] * imp_factor
    return docs_and_scores # return a map containing documents and their scores

def serve_query(query_token_frequencies, index_file, index_for_index):
    all_query_postings = []
    query_tf_idfs = []
    query_leng_for_normalize = 0
    #check if query exceeds 32 tokens (if it does only consider the longest 32 tokens in the query)
    if len(query_token_frequencies) <= 32:
        query_items = query_token_frequencies.items()
    else:
        query_items = sorted(list(query_token_frequencies.items()), key = lambda item: len(item[0]), reverse = True)[:32]
    #go through each query token and find their postings, compute norm tf-idf for query using ltc
    for token, freq in query_items:
        if token in index_for_index:
            index_file.seek(index_for_index[token])
            line = index_file.readline().strip()
            term, postings = line.split(":")
            postings = convert_str_to_postings2(postings) # turns string into postings list
            all_query_postings.append((term, postings))
            tf_idf = compute_tf_idf(freq, len(postings), lambda tf: 1+math.log10(tf), lambda df: math.log10(N/df)) #ltc #can consider limiting to terms with high idf only
            query_tf_idfs.append(tf_idf)
            query_leng_for_normalize += tf_idf ** 2
    query_leng_for_normalize = math.sqrt(query_leng_for_normalize)
    query_norm_tf_idfs = [tf_idf/query_leng_for_normalize for tf_idf in query_tf_idfs]
    docs_and_scores = get_docs_and_scores(all_query_postings, query_norm_tf_idfs) #pass in query_postings and query normalized tf_idfs to get ranking
    result = get_top_5_queries_from_docs_and_scores(docs_and_scores)
    return result

def print_top_5(results, doc_id_url_map):
    if len(results) == 0:
        print("No results found")
    else:
        i = 0
        for item in heapq.nlargest(5, results):
            print(f"{i+1}. {doc_id_url_map[str(item[1])]}")
            i += 1
    

if __name__ == "__main__":
    with open(os.path.join("Auxilary", "DocID_map.json"), "r") as file:
        doc_id_url_map = json.load(file)
    # open doc_id_url_map to allow us to print urls from top 5 docids
    with open(os.path.join("Auxilary", "index_for_index.json"), "r") as file:
        index_for_index = json.load(file)
    # open index_for_index so we can use to find terms that we need to look up in the index
    with open(os.path.join("Merge", "final_full_index.txt"), "r") as file:
        while True:
            query = input("Enter a query: ")
            start_time = time.time()
            if len(query) != 0:
                query_tokens = tokenize(query)
                query_token_frequencies = compute_token_frequencies(query_tokens)
                results = serve_query(query_token_frequencies, file, index_for_index)
                print_top_5(results, doc_id_url_map)
            else:
                break
            end_time = time.time()
            resp_time = (end_time-start_time) * 1000
            print(f"Response time to query was {resp_time} ms.")