from retrieval.retriever import search


def retrieve(doc_index, query, k=None):
    """Top-k chunks with scores, plus the joined context text."""
    hits = search(doc_index, query, k)
    context = "\n\n".join(h["text"] for h in hits)
    return hits, context
