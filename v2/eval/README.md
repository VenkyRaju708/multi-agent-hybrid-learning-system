# Evaluation

This folder measures the tutor on a fixed set of questions: how often it
routes a question correctly, how faithful and relevant its answers are, and
how long each stage takes. Run it on your own machine with Ollama and Llama 3,
the same setup the app uses.

## 1. Build the question set (100 questions)

Copy `questions_template.csv` to `questions.csv` and replace the six EXAMPLE
rows with your own. Aim for this split:

| Type | Count | What it is | `expected_route` |
|---|---|---|---|
| Document-specific | 40 | Answerable only from the uploaded document | `document` |
| General knowledge | 40 | Answerable without the document | `topic` |
| Mixed intent | 20 | Needs the document and general knowledge | `mixed` |

Rules that keep the result honest:

- Put a document in `pdf_file` for **every** row, topic questions included.
  With no document loaded the router chooses Topic mode by rule, so a topic
  question asked without a document tests nothing.
- Use one to three real documents (lecture notes, a paper, a manual). Put the
  files next to `questions.csv` or give absolute paths.
- Write the questions and labels **before** you run anything, and don't change
  a label after seeing the result.
- `reference_points`: the key facts a good answer contains, separated by `;`.
  They guide the judge and your own spot checks.
- Ambiguous cases belong in the mixed group; label each by what a careful
  human would expect.

Columns: `id, question, type, expected_route, pdf_file, reference_points, notes`.

## 2. Run the questions

From the project root, with Ollama running:

```
python eval/run_eval.py --questions eval/questions.csv --out eval/results.jsonl --baselines
```

- `--baselines` also records what three simple routers would have chosen:
  always document, always topic, and the April 2026 rule (document whenever a
  PDF is loaded).
- `--no-tts` skips speech synthesis, which is faster when you only need routing
  and answer quality. Keep TTS on for the latency run you report.
- `--limit 5` runs a quick trial first.

Each line of `results.jsonl` records the route and how it was chosen, the
retrieved chunks with similarity scores, the answer, the notes and the seconds
spent in each stage. A question that fails is logged with its error; keep
failures in the results.

## 3. Score

```
python eval/score.py --results eval/results.jsonl --out-dir eval/report --judge
```

This writes to `eval/report/`:

- `results.md`: routing accuracy (clear-intent and mixed reported separately,
  plus the baselines), a confusion matrix, latency median and 90th percentile
  per stage, and with `--judge` the faithfulness and relevance scores.
- `judge_prompt.txt`: the exact prompt the LLM judge used. Report it with the
  results.
- `spot_check.csv`: every question with its answer and the judge's verdict,
  plus empty columns for your own checks.

Routing accuracy = correctly routed queries / total evaluated queries x 100.

The judge is the same Llama 3 model, so treat its scores as indicative. Check
at least 20 rows of `spot_check.csv` by hand and report how often you agreed
with the judge.

Every number in the report comes from `results.jsonl`. If `results.md` starts
with a MOCK BACKEND warning, the run used the test model; don't report it.
