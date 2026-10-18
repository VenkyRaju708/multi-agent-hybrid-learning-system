"""Sentence embeddings, normalized so inner product = cosine similarity.

AVT_EMBED=hash selects a deterministic bag-of-words hashing embedder that
needs no download; it exists for tests and is not used for evaluation.
"""
import hashlib
import re

import numpy as np

import config

_model = None
_HASH_DIM = 256


def _hash_embed(texts):
    out = np.zeros((len(texts), _HASH_DIM), dtype="float32")
    for i, t in enumerate(texts):
        for w in re.findall(r"[a-z0-9]+", t.lower()):
            h = int(hashlib.md5(w.encode()).hexdigest(), 16)
            out[i, h % _HASH_DIM] += 1.0
    return out


def embed(texts):
    if config.EMBED_BACKEND == "hash":
        vecs = _hash_embed(texts)
    else:
        global _model
        if _model is None:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(config.EMBED_MODEL)
        vecs = np.asarray(_model.encode(texts), dtype="float32")
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms
