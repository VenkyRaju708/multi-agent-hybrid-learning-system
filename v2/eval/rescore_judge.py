"""Rebuild the report from the judge replies already in judge.jsonl, parsing them more tolerantly.

Usage:
    python eval/rescore_judge.py --results eval/results_combined.jsonl \
        --judge eval/report/judge.jsonl --out-dir eval/report_rescored \
        [--human eval/report/spot_check_human_ratings.csv]

No judge calls are made: each verdict is the original reply, re-read. The only
parsing change from score.py is that a reply missing its closing brace is
completed with "}" before parsing (Llama 3 sometimes stops just before it).
The source report is not modified. Routing and latency tables are recomputed
from the same results file, so they match the original report.
"""
import argparse
import csv
import json
import os

import score


def parse_reply(reply):
    """Return the judge's JSON object, or None. Tolerates a missing closing brace."""
    if "{" not in reply:
        return None
    body = reply[reply.index("{"):]
    candidates = [body[: body.rindex("}") + 1]] if "}" in body else []
    candidates.append(body.rstrip() + "}")
    for text in candidates:
        try:
            return json.loads(text)
        except ValueError:
            continue
    return None


def verdict_from(r, reply):
    verdict = {"id": r["id"], "raw": reply, "faithfulness": None,
               "relevance": None, "comment": "", "reparsed": False}
    data = parse_reply(reply)
    if data is not None:
        try:
            f_val = str(data.get("faithfulness", "")).lower()
            verdict["faithfulness"] = f_val if f_val in ("yes", "partial", "no", "n/a") else None
            rel = int(data.get("relevance"))
            verdict["relevance"] = rel if 1 <= rel <= 5 else None
            verdict["comment"] = str(data.get("comment", ""))
        except (ValueError, TypeError):
            pass
    if not r.get("chunks"):
        verdict["faithfulness"] = "n/a"
    return verdict


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--results", required=True)
    p.add_argument("--judge", required=True, help="judge.jsonl from the original score.py --judge run")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--human", help="spot_check CSV with human ratings to carry over")
    a = p.parse_args(argv)
    if os.path.abspath(a.out_dir) == os.path.abspath(os.path.dirname(a.judge)):
        raise SystemExit("--out-dir must differ from the original report folder")

    with open(a.judge, encoding="utf-8") as f:
        original = {v["id"]: v for v in (json.loads(line) for line in f if line.strip())}

    def run_judge_from_file(rows, out_dir):
        with open(os.path.join(out_dir, "judge_prompt.txt"), "w", encoding="utf-8") as f:
            f.write(score.JUDGE_PROMPT)
        judged = []
        for r in rows:
            v = verdict_from(r, original[r["id"]]["raw"])
            v["reparsed"] = original[r["id"]].get("relevance") is None and v["relevance"] is not None
            judged.append(v)
        with open(os.path.join(out_dir, "judge.jsonl"), "w", encoding="utf-8") as f:
            for v in judged:
                f.write(json.dumps(v, ensure_ascii=False) + "\n")
        return {v["id"]: v for v in judged}

    score.run_judge = run_judge_from_file
    md_path = score.report(a.results, a.out_dir, judge=True)

    with open(os.path.join(a.out_dir, "judge.jsonl"), encoding="utf-8") as f:
        reparsed = [v["id"] for v in (json.loads(line) for line in f) if v["reparsed"]]
    with open(md_path, encoding="utf-8") as f:
        body = f.read()
    note = ("> **Evaluation V2 (re-parsed judge replies).** Same results file and the same judge "
            f"replies as V1 (`{os.path.relpath(a.judge, a.out_dir)}`); no judge calls were made. "
            f"{len(reparsed)} replies that V1 could not parse because the closing brace was missing "
            f"are now included: {', '.join(reparsed) or 'none'}. All other verdicts are unchanged.\n\n")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(body.replace("# Evaluation results\n\n", "# Evaluation results (V2)\n\n" + note, 1))

    if a.human:
        out_csv = os.path.join(a.out_dir, "spot_check.csv")
        with open(a.human, newline="", encoding="utf-8") as f:
            human = {r["id"]: r for r in csv.DictReader(f)}
        with open(out_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fields, rows = reader.fieldnames, list(reader)
        cols = ["human_route_ok", "human_faithfulness", "human_relevance", "human_comment"]
        for r in rows:
            for c in cols:
                r[c] = human.get(r["id"], {}).get(c, "")
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    print(f"Wrote {md_path}; re-parsed: {reparsed}")


if __name__ == "__main__":
    main()
