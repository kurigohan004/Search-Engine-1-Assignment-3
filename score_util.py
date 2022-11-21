def compute_tf_idf(term_frequency, doc_frequency, tf_func, idf_func):
    return tf_func(term_frequency) * idf_func(doc_frequency)