import sys

def get_num_indexed_docs(curr_doc_id):
    return curr_doc_id #might need to change

def get_num_unique_toks(inv_index):
    return len(inv_index) #might need to change

def get_size_index(inv_index):
    return sys.getsizeof(inv_index) / 1000 #might need to change