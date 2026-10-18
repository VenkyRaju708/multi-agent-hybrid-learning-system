"""Score a results.jsonl file produced by run_eval.py.

Usage:
    python eval/score.py --results eval/results.jsonl --out-dir eval/report [--judge]

Writes results.md (tables), spot_check.csv (for human review) and, with
--judge, judge_prompt.txt plus judge.jsonl. Every number comes from the
results file; nothing is estimated or filled in.
"""
import argparse
import csv
import json
import os
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(os.path.dirname(HERE), "agentic_voice_tutor")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

LABELS = ["document", "topic", "mixed"]
STAGES = ["ingest", "stt", "route", "retrieve", "generate", "summarize", "tts", "total"]

JUDGE_PROMPT = """JUDGE_TASK
You are grading a study assistant's answer. Reply with JSON only:
{{"faithfulness": "yes" | "partial" | "no" | "n/a", "relevance": 1-5, "comment": "<one sentence>"}}

faithfulness: is every factual claim in the ANSWER supported by the RETRIEVED CHUNKS?
  Use "n/a" when there are no retrieved chunks.
relevance: how well does the ANSWER address the QUESTION? 1 = not at all, 5 = fully.
Key points a good answer should contain (may be empty): {reference_points}

QUESTION: {question}

RETRIEVED CHUNKS:
{chunks}

ANSWER:
{answer}"""


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def accuracy(rows, key="predicted_route"):
    """Routing accuracy = correctly routed / total evaluated x 100."""
    if not rows:
        return None, 0, 0
    correct = sum(1 for r in rows if r.get(key) == r.get("expected_route"))
    return 100.0 * correct / len(rows), correct, len(rows)


def baseline_accuracy(rows, name):
    if not rows:
        return None, 0, 0
    correct = sum(1 for r in rows if r.get("baselines", {}).get(name) == r.get("expected_route"))
    return 100.0 * correct / len(rows), correct, len(rows)


def confusion(rows):
    m = {e: Counter() for e in LABELS}
    for r in rows:
        if r.get("expected_route") in m:
            m[r["expected_route"]][r.get("predicted_route")] += 1
    return m


def latency(rows):
    out = {}
    for s in STAGES:
        vals = [r["timings"][s] for r in rows if s in r.get("timings", {})]
        if vals:
            out[s] = (len(vals), float(np.median(vals)), float(np.percentile(vals, 90)))
    return out


def _fmt_acc(acc):
    value, correct, n = acc
    return "—" if value is None else f"{value:.1f}% ({correct}/{n})"


def run_judge(rows, out_dir):
    from llm.ollama_client import generate

    with open(os.path.join(out_dir, "judge_prompt.txt"), "w", encoding="utf-8") as f:
        f.write(JUDGE_PROMPT)
    judged = []
    for r in rows:
        chunks = "\n---\n".join(c["text"] for c in r.get("chunks") or []) or "(none)"
        prompt = JUDGE_PROMPT.format(reference_points=r.get("reference_points", ""),
                                     question=r["question"], chunks=chunks,
                                     answer=r.get("answer", ""))
        reply = generate(prompt)
        verdict = {"id": r["id"], "raw": reply, "faithfulness": None,
                   "relevance": None, "comment": ""}
        try:
            start, end = reply.index("{"), reply.rindex("}") + 1
            data = json.loads(reply[start:end])
            f_val = str(data.get("faithfulness", "")).lower()
            verdict["faithfulness"] = f_val if f_val in ("yes", "partial", "no", "n/a") else None
            rel = int(data.get("relevance"))
            verdict["relevance"] = rel if 1 <= rel <= 5 else None
            verdict["comment"] = str(data.get("comment", ""))
        except (ValueError, TypeError):
            pass
        if not r.get("chunks"):
            verdict["faithfulness"] = "n/a"
        judged.append(verdict)
    with open(os.path.join(out_dir, "judge.jsonl"), "w", encoding="utf-8") as f:
        for v in judged:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")
    return {v["id"]: v for v in judged}


def report(results_path, out_dir, judge=False):
    os.makedirs(out_dir, exist_ok=True)
    allrows = load(results_path)
    rows = [r for r in allrows if not r.get("error")]
    errors = [r for r in allrows if r.get("error")]
    clear = [r for r in rows if r.get("type") in ("document", "topic")]
    mixed = [r for r in rows if r.get("type") == "mixed"]
    backends = sorted({r.get("llm_backend", "?") for r in rows})
    has_baselines = any("baselines" in r for r in rows)

    lines = ["# Evaluation results", ""]
    if "mock" in backends:
        lines += ["> **MOCK BACKEND: these numbers come from the test model and are "
                  "not real results. Do not report them.**", ""]
    lines += [f"Results file: `{os.path.basename(results_path)}` · LLM: {', '.join(backends)} · "
              f"questions run: {len(allrows)} · errors: {len(errors)}", ""]

    lines += ["## Routing accuracy", "",
              "Routing accuracy = correctly routed queries / total evaluated queries x 100", "",
              "| System | Clear intent (document + topic) | Mixed | All |",
              "|---|---|---|---|",
              f"| Multi-agent router | {_fmt_acc(accuracy(clear))} | {_fmt_acc(accuracy(mixed))} | {_fmt_acc(accuracy(rows))} |"]
    if has_baselines:
        for name, title in (("original_rule", "Original rule (PDF uploaded?)"),
                            ("always_document", "Always document"),
                            ("always_topic", "Always topic")):
            lines.append(f"| {title} | {_fmt_acc(baseline_accuracy(clear, name))} | "
                         f"{_fmt_acc(baseline_accuracy(mixed, name))} | {_fmt_acc(baseline_accuracy(rows, name))} |")
    fb = sum(1 for r in rows if r.get("fallback"))
    lines += ["", f"Similarity fallback used on {fb} of {len(rows)} questions.", ""]

    m = confusion(rows)
    lines += ["### Confusion matrix (rows = expected, columns = predicted)", "",
              "| Expected \\ Predicted | " + " | ".join(LABELS) + " |",
              "|---|" + "---|" * len(LABELS)]
    for e in LABELS:
        lines.append(f"| {e} | " + " | ".join(str(m[e][p]) for p in LABELS) + " |")
    lines.append("")

    lat = latency(rows)
    lines += ["## Latency (seconds)", "", "| Stage | n | Median | 90th percentile |", "|---|---|---|---|"]
    for s in STAGES:
        if s in lat:
            n, med, p90 = lat[s]
            lines.append(f"| {s} | {n} | {med:.2f} | {p90:.2f} |")
    lines += ["", "`total` = query to finished answer (route, retrieve, generate, summarize, tts); "
              "`ingest` is counted once per document.", ""]

    verdicts = {}
    if judge:
        verdicts = run_judge(rows, out_dir)
        faith = [v["faithfulness"] for v in verdicts.values() if v["faithfulness"] in ("yes", "partial", "no")]
        rel = [v["relevance"] for v in verdicts.values() if v["relevance"] is not None]
        c = Counter(faith)
        lines += ["## LLM-judge scores", "",
                  "Judge prompt: `judge_prompt.txt`. Spot-check a sample by hand (`spot_check.csv`) "
                  "before reporting these.", "",
                  "| Measure | Result |", "|---|---|"]
        if faith:
            for k in ("yes", "partial", "no"):
                lines.append(f"| Faithfulness: {k} | {c[k]} of {len(faith)} ({100.0 * c[k] / len(faith):.1f}%) |")
        else:
            lines.append("| Faithfulness | no judged answers with retrieved chunks |")
        if rel:
            lines.append(f"| Relevance (1-5), mean | {np.mean(rel):.2f} over {len(rel)} answers |")
        unparsed = sum(1 for v in verdicts.values() if v["relevance"] is None)
        lines += ["", f"Judge replies that could not be parsed: {unparsed}.", ""]

    if errors:
        lines += ["## Errors", "", "| id | error |", "|---|---|"]
        lines += [f"| {r['id']} | {str(r['error']).replace('|', '/')} |" for r in errors]
        lines.append("")

    with open(os.path.join(out_dir, "results.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    with open(os.path.join(out_dir, "spot_check.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "question", "expected_route", "predicted_route",
                    "route_method", "answer", "retrieved_chunks", "reference_points",
                    "judge_faithfulness", "judge_relevance", "human_route_ok",
                    "human_faithfulness", "human_relevance", "human_comment"])
        for r in rows:
            v = verdicts.get(r["id"], {})
            chunks = " || ".join(f"[{c['score']:.2f}] {c['text'][:300]}" for c in r.get("chunks") or [])
            w.writerow([r["id"], r.get("type"), r["question"], r.get("expected_route"),
                        r.get("predicted_route"), r.get("route_method"), r.get("answer"),
                        chunks, r.get("reference_points"), v.get("faithfulness", ""),
                        v.get("relevance", ""), "", "", "", ""])
    return os.path.join(out_dir, "results.md")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--results", required=True)
    p.add_argument("--out-dir", default="report")
    p.add_argument("--judge", action="store_true", help="also run the LLM judge")
    a = p.parse_args(argv)
    path = report(a.results, a.out_dir, judge=a.judge)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
