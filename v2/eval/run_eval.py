"""Run the question set through the pipeline and log every result as JSONL.

Usage (from the project root, with Ollama running):
    python eval/run_eval.py --questions eval/questions.csv --out eval/results.jsonl --baselines

Each line records the route decision, retrieved chunks with scores, the
answer, the notes and per-stage latencies. Nothing is scored here; run
eval/score.py on the output.
"""
import argparse
import csv
import json
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(os.path.dirname(HERE), "agentic_voice_tutor")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from agents.router_agent import original_rule  # noqa: E402
from pipeline import Timings, answer, load_document  # noqa: E402

FIELDS = ["id", "question", "type", "expected_route", "pdf_file",
          "reference_points", "notes"]


def read_questions(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    missing = [c for c in FIELDS if rows and c not in rows[0]]
    if missing:
        raise SystemExit(f"{path} is missing columns: {', '.join(missing)}")
    return rows


def run(questions_path, out_path, tts=True, notes=True, baselines=False,
        limit=None):
    rows = read_questions(questions_path)
    if limit:
        rows = rows[:limit]
    base_dir = os.path.dirname(os.path.abspath(questions_path))
    indexes = {}
    written = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for row in rows:
            record = {k: row.get(k, "") for k in FIELDS}
            record["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            try:
                timings = Timings()
                doc_index, cache_hit = None, None
                pdf = (row.get("pdf_file") or "").strip()
                if pdf:
                    path = pdf if os.path.isabs(pdf) else os.path.join(base_dir, pdf)
                    if path not in indexes:
                        with open(path, "rb") as f:
                            data = f.read()
                        indexes[path], cache_hit = load_document(
                            data, os.path.basename(path), timings)
                    else:
                        cache_hit = True
                    doc_index = indexes[path]
                result = answer(row["question"], doc_index, notes=notes,
                                tts=tts, timings=timings)
                route = result["route"]
                record.update({
                    "predicted_route": route["label"],
                    "answered_as": result["answered_as"],
                    "route_method": route["method"],
                    "fallback": route["fallback"],
                    "best_score": route["best_score"],
                    "route_reason": route["reason"],
                    "chunks": result["chunks"],
                    "answer": result["answer"],
                    "generated_notes": result["notes"],
                    "timings": result["timings"],
                    "ingest_cache_hit": cache_hit,
                    "llm_backend": result["llm_backend"],
                    "error": None,
                })
                if baselines:
                    has_doc = doc_index is not None and len(doc_index) > 0
                    record["baselines"] = {
                        "always_document": "document",
                        "always_topic": "topic",
                        "original_rule": original_rule(has_doc),
                    }
            except Exception as exc:  # keep going; failures are results too
                record.update({"error": f"{type(exc).__name__}: {exc}",
                               "traceback": traceback.format_exc()})
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            written += 1
            status = record.get("predicted_route") or ("ERROR " + str(record.get("error")))
            print(f"[{written}/{len(rows)}] {record['id']}: {status}")
    return written


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--questions", required=True, help="CSV in the questions_template.csv format")
    p.add_argument("--out", default="results.jsonl")
    p.add_argument("--no-tts", action="store_true", help="skip speech synthesis")
    p.add_argument("--no-notes", action="store_true", help="skip the notes agent")
    p.add_argument("--baselines", action="store_true",
                   help="also record always-document, always-topic and the original rule")
    p.add_argument("--limit", type=int, default=None, help="run only the first N questions")
    a = p.parse_args(argv)
    n = run(a.questions, a.out, tts=not a.no_tts, notes=not a.no_notes,
            baselines=a.baselines, limit=a.limit)
    print(f"Wrote {n} records to {a.out}")


if __name__ == "__main__":
    main()
