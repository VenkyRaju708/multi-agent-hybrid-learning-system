import csv
import json
import os
import shutil

import run_eval
import score

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), "eval", "questions_template.csv")


def _questions(tmp_path, sample_doc):
    shutil.copy(sample_doc, tmp_path / "your_document.txt")
    out = tmp_path / "questions.csv"
    with open(TEMPLATE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 6
    assert all(r["id"].startswith("EXAMPLE") for r in rows)
    assert sorted(r["type"] for r in rows) == ["document"] * 2 + ["mixed"] * 2 + ["topic"] * 2
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        for r in rows:
            r["pdf_file"] = "your_document.txt"
            w.writerow(r)
    return out


def test_run_eval_and_score_on_examples(tmp_path, sample_doc):
    questions = _questions(tmp_path, sample_doc)
    results = tmp_path / "results.jsonl"
    n = run_eval.run(str(questions), str(results), tts=False, baselines=True)
    assert n == 6
    records = [json.loads(l) for l in results.read_text(encoding="utf-8").splitlines()]
    assert all(r["error"] is None for r in records)
    assert all(r["llm_backend"] == "mock" for r in records)
    assert all(set(r["baselines"]) == {"always_document", "always_topic", "original_rule"}
               for r in records)
    assert records[0]["ingest_cache_hit"] is False
    assert all(r["ingest_cache_hit"] for r in records[1:])
    for r in records:
        assert {"route", "generate", "summarize", "total"} <= set(r["timings"])

    out_dir = tmp_path / "report"
    md_path = score.report(str(results), str(out_dir), judge=True)
    md = open(md_path, encoding="utf-8").read()
    assert "MOCK BACKEND" in md
    assert "Routing accuracy" in md and "Confusion matrix" in md
    assert "Original rule (PDF uploaded?)" in md
    assert (out_dir / "judge_prompt.txt").exists()
    with open(out_dir / "spot_check.csv", newline="", encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 6


def test_accuracy_formula():
    rows = [{"expected_route": "document", "predicted_route": "document"},
            {"expected_route": "topic", "predicted_route": "document"},
            {"expected_route": "topic", "predicted_route": "topic"},
            {"expected_route": "mixed", "predicted_route": "mixed"}]
    value, correct, total = score.accuracy(rows)
    assert (correct, total) == (3, 4) and value == 75.0
    assert score.accuracy([]) == (None, 0, 0)


def test_errors_are_recorded_not_raised(tmp_path):
    q = tmp_path / "q.csv"
    q.write_text("id,question,type,expected_route,pdf_file,reference_points,notes\n"
                 "X1,What?,document,document,missing.pdf,,\n", encoding="utf-8")
    results = tmp_path / "r.jsonl"
    run_eval.run(str(q), str(results), tts=False)
    rec = json.loads(results.read_text(encoding="utf-8"))
    assert rec["error"] and "FileNotFoundError" in rec["error"]
