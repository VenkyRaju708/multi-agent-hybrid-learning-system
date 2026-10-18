import json

from agents import router_agent
from agents.router_agent import original_rule, route_query, similarity_route
from ingestion.chunker import chunk_text
from pipeline import Timings, answer, load_document
from retrieval.vector_store import get_or_build


def _index(sample_doc):
    data = sample_doc.read_bytes()
    index, _ = get_or_build(data, sample_doc.name)
    return index


# --- chunking ---------------------------------------------------------------

def test_chunk_overlap():
    words = [f"w{i}" for i in range(1200)]
    chunks = chunk_text(" ".join(words), size=500, overlap=50)
    assert [len(c.split()) for c in chunks] == [500, 500, 300]
    first, second = chunks[0].split(), chunks[1].split()
    assert first[-50:] == second[:50]
    assert chunks[-1].split()[-1] == "w1199"


def test_chunk_no_overlap_short_text():
    assert chunk_text("a b c", size=500, overlap=50) == ["a b c"]
    assert chunk_text("", size=500, overlap=50) == []


# --- cache --------------------------------------------------------------------

def test_index_cache_reused(sample_doc):
    data = sample_doc.read_bytes()
    first, hit1 = get_or_build(data, "sample.txt")
    second, hit2 = get_or_build(data, "sample.txt")
    assert hit1 is False and hit2 is True
    assert first is second
    other, hit3 = get_or_build(data + b" extra words", "sample.txt")
    assert hit3 is False and other is not first


# --- routing --------------------------------------------------------------------

def test_no_document_routes_topic_without_llm(monkeypatch):
    called = []
    monkeypatch.setattr(router_agent, "generate", lambda *a, **k: called.append(1))
    route = route_query("What is gravity?", None)
    assert route["label"] == "topic" and route["method"] == "no_document"
    assert not route["fallback"] and called == []


def test_llm_router_labels(sample_doc):
    index = _index(sample_doc)
    assert route_query("What do my notes say?", index)["label"] == "document"
    assert route_query("Who wrote Hamlet?", index)["label"] == "topic"
    r = route_query("mixed question please", index)
    assert r["label"] == "mixed" and r["method"] == "llm" and not r["fallback"]


def test_unparsable_reply_uses_similarity_fallback(sample_doc):
    index = _index(sample_doc)
    on_topic = route_query("unparsable Calvin cycle fixes carbon dioxide", index)
    assert on_topic["fallback"] and on_topic["method"] == "similarity_fallback"
    assert on_topic["label"] == similarity_route(on_topic["best_score"])
    off_topic = route_query("unparsable zebra xylophone quantum", index)
    assert off_topic["fallback"] and off_topic["label"] == "topic"


def test_invalid_label_is_rejected(sample_doc, monkeypatch):
    index = _index(sample_doc)
    monkeypatch.setattr(router_agent, "generate",
                        lambda *a, **k: json.dumps({"label": "banana"}))
    assert route_query("anything", index)["fallback"] is True


def test_similarity_thresholds():
    assert similarity_route(0.9) == "document"
    assert similarity_route(0.35) == "mixed"
    assert similarity_route(0.05) == "topic"


def test_original_rule():
    assert original_rule(True) == "document" and original_rule(False) == "topic"


# --- pipeline -------------------------------------------------------------------

def test_mixed_path_merges_and_retrieves(sample_doc):
    index = _index(sample_doc)
    result = answer("mixed: explain the Calvin cycle", index)
    assert result["answered_as"] == "mixed"
    assert result["answer"] == "MOCK merged answer."
    assert result["chunks"] and all("score" in c for c in result["chunks"])
    assert len(result["chunks"]) <= 3
    for stage in ("route", "retrieve", "generate", "summarize", "total"):
        assert stage in result["timings"]


def test_document_path_and_topic_path(sample_doc):
    index = _index(sample_doc)
    doc = answer("What do my notes say about ATP?", index)
    assert doc["answered_as"] == "document" and doc["chunks"]
    topic = answer("What is gravity?", None)
    assert topic["answered_as"] == "topic" and topic["chunks"] == []


def test_load_document_timed(sample_doc):
    t = Timings()
    _, hit = load_document(sample_doc.read_bytes(), sample_doc.name, t)
    assert hit is False and "ingest" in t


def test_real_pdf_ingestion(tmp_path):
    from reportlab.pdfgen import canvas

    pdf = tmp_path / "doc.pdf"
    c = canvas.Canvas(str(pdf))
    c.drawString(72, 720, "The Calvin cycle fixes carbon dioxide into sugar.")
    c.showPage()
    c.drawString(72, 720, "Light reactions produce ATP and NADPH.")
    c.save()
    index, hit = get_or_build(pdf.read_bytes(), "doc.pdf")
    assert hit is False and len(index) == 1
    assert "Calvin" in index.chunks[0] and "NADPH" in index.chunks[0]


def test_similarity_fallback_can_choose_document():
    index, _ = get_or_build(b"The Calvin cycle fixes carbon dioxide into sugar.", "short.txt")
    route = route_query("unparsable Calvin cycle fixes carbon dioxide into sugar", index)
    assert route["fallback"] and route["best_score"] >= 0.45
    assert route["label"] == "document"
