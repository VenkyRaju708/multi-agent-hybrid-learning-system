"""FAISS index per document, cached by the SHA-256 of the uploaded bytes.

The April 2026 prototype rebuilt one global index on every question; this
version builds each document's index once and reuses it.
"""
import hashlib

import faiss
import numpy as np

from ingestion.chunker import chunk_text
from ingestion.pdf_parser import load_document_bytes
from retrieval.embeddings import embed


class DocumentIndex:
    def __init__(self, doc_id, chunks):
        self.doc_id = doc_id
        self.chunks = chunks
        vecs = embed(chunks) if chunks else np.zeros((0, 1), dtype="float32")
        self.index = faiss.IndexFlatIP(vecs.shape[1])
        if chunks:
            self.index.add(vecs)

    def __len__(self):
        return len(self.chunks)


_CACHE = {}


def doc_id_for(data):
    return hashlib.sha256(data).hexdigest()


def get_or_build(data, filename=""):
    """Return (DocumentIndex, cache_hit) for the uploaded bytes."""
    key = doc_id_for(data)
    if key in _CACHE:
        return _CACHE[key], True
    text = load_document_bytes(data, filename)
    index = DocumentIndex(key, chunk_text(text))
    _CACHE[key] = index
    return index, False


def clear_cache():
    _CACHE.clear()
