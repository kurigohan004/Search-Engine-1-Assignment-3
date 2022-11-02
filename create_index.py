from indexer import DOC_ID, build_index
from analytics import *


def create_report(inv_index): #might need to change
    with open("report.txt", "w") as file:
        file.write(f"The number of indexed documents: {get_num_indexed_docs(DOC_ID)}\n\n")

        file.write(f"The number of unique tokens: {get_num_unique_toks(inv_index)}\n\n")

        file.write(f"The total size (in KB) of index on disk: {get_size_index(inv_index)}\n")


if __name__ == "__main__":
    pass