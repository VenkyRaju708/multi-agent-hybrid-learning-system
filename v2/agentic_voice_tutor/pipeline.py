"""Headless question-answering pipeline used by the app and the evaluation.

answer() returns everything needed to inspect a run: the route decision,
retrieved chunks with scores, the answer, the notes and per-stage timings.
"""
import time

from agents.notes_agent import generate_notes
from agents.router_agent import route_query
from llm.ollama_client import backend_name
from modes.document_mode import handle_document
from modes.mixed_mode import handle_mixed
from modes.topic_mode import handle_topic
from retrieval.vector_store import get_or_build


class Timings(dict):
    """Seconds per stage; stages: ingest, stt, route, retrieve, generate,
    summarize, tts, total."""

    def measure(self, stage, fn, *args, **kwargs):
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            self[stage] = self.get(stage, 0.0) + time.perf_counter() - start


def load_document(data, filename, timings=None):
    """Index an uploaded document (cached). Returns (index, cache_hit)."""
    timings = Timings() if timings is None else timings
    return timings.measure("ingest", get_or_build, data, filename)


def answer(query, doc_index=None, route_override=None, notes=True,
           tts=False, timings=None):
    timings = Timings() if timings is None else timings
    start = time.perf_counter()

    if route_override:
        route = {"label": route_override, "reason": "forced for evaluation",
                 "method": "override", "fallback": False, "best_score": None}
    else:
        route = timings.measure("route", route_query, query, doc_index)

    label = route["label"]
    if label != "topic" and (doc_index is None or len(doc_index) == 0):
        label = "topic"  # nothing to retrieve from
    if label == "document":
        response, hits = handle_document(query, doc_index, timings)
    elif label == "mixed":
        response, hits = handle_mixed(query, doc_index, timings)
    else:
        response, hits = handle_topic(query, timings)

    note_text = timings.measure("summarize", generate_notes, response) if notes else ""

    audio_path = None
    if tts:
        from llm.tts_engine import synthesize_to_wav

        audio_path = timings.measure("tts", synthesize_to_wav, response)

    # "total" = query to answer (route + retrieve + generate + summarize + tts);
    # ingest and stt are recorded separately because they happen before.
    timings["total"] = time.perf_counter() - start
    return {
        "route": route,
        "answered_as": label,
        "chunks": hits,
        "answer": response,
        "notes": note_text,
        "audio_path": audio_path,
        "timings": dict(timings),
        "llm_backend": backend_name(),
    }
