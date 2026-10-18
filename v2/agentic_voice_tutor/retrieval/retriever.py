import numpy as np

import config
from retrieval.embeddings import embed


def search(doc_index, query, k=None):
    """Top-k chunks for the query as a list of {"text", "score"} (cosine)."""
    k = config.TOP_K if k is None else k
    if doc_index is None or len(doc_index) == 0:
        return []
    k = min(k, len(doc_index))
    q = embed([query])
    scores, idx = doc_index.index.search(np.asarray(q, dtype="float32"), k)
    return [{"text": doc_index.chunks[i], "score": float(s)}
            for s, i in zip(scores[0], idx[0]) if i >= 0]
