"""Coordination agent: decides whether a query is about the uploaded
document, a general topic, or both.

Order of decisions:
1. No document loaded            -> "topic", no LLM call (method "no_document").
2. LLM few-shot JSON classifier  -> "document" | "topic" | "mixed" (method "llm").
3. LLM reply unusable            -> similarity heuristic on the best FAISS
                                    score (method "similarity_fallback").
"""
import json
import re

import config
from llm.ollama_client import generate
from retrieval.retriever import search

LABELS = ("document", "topic", "mixed")

ROUTER_PROMPT = """ROUTER_TASK
You route questions in a study assistant. The learner has uploaded a document
titled or about: {doc_hint}

Answer with JSON only: {{"label": "document" | "topic" | "mixed", "reason": "<one short sentence>"}}
- "document": the answer must come from the uploaded document.
- "topic": a general question the document is not needed for.
- "mixed": needs the document AND general knowledge.

Examples:
Query: What does section 3 of my notes say about photosynthesis?
{{"label": "document", "reason": "Asks about the uploaded notes."}}
Query: What is the capital of France?
{{"label": "topic", "reason": "General knowledge, unrelated to the document."}}
Query: Summarize the method in my PDF and explain how it compares to standard practice.
{{"label": "mixed", "reason": "Needs the document and outside knowledge."}}

Query: {query}"""


def _parse(reply):
    match = re.search(r"\{.*?\}", reply or "", re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except ValueError:
        return None
    label = str(data.get("label", "")).strip().lower()
    if label not in LABELS:
        return None
    return label, str(data.get("reason", "")).strip()


def similarity_route(best_score):
    if best_score >= config.ROUTER_DOC_THRESHOLD:
        return "document"
    if best_score >= config.ROUTER_MIXED_THRESHOLD:
        return "mixed"
    return "topic"


def route_query(query, doc_index=None, doc_hint=""):
    """Return {"label", "reason", "method", "fallback", "best_score"}."""
    if doc_index is None or len(doc_index) == 0:
        return {"label": "topic", "reason": "No document loaded.",
                "method": "no_document", "fallback": False, "best_score": None}

    hits = search(doc_index, query, k=1)
    best = hits[0]["score"] if hits else 0.0
    hint = doc_hint or (doc_index.chunks[0][:200] if doc_index.chunks else "")

    reply = generate(ROUTER_PROMPT.format(doc_hint=hint, query=query))
    parsed = _parse(reply)
    if parsed:
        label, reason = parsed
        return {"label": label, "reason": reason, "method": "llm",
                "fallback": False, "best_score": best}

    label = similarity_route(best)
    return {"label": label,
            "reason": f"LLM reply unusable; best chunk similarity {best:.2f}.",
            "method": "similarity_fallback", "fallback": True,
            "best_score": best}


def original_rule(has_document):
    """The April 2026 prototype's rule, kept as an evaluation baseline."""
    return "document" if has_document else "topic"
