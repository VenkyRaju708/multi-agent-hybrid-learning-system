# Evaluation results

Results file: `results_combined.jsonl` · LLM: ollama:llama3 · questions run: 100 · errors: 0

## Routing accuracy

Routing accuracy = correctly routed queries / total evaluated queries x 100

| System | Clear intent (document + topic) | Mixed | All |
|---|---|---|---|
| Multi-agent router | 92.5% (74/80) | 100.0% (20/20) | 94.0% (94/100) |
| Original rule (PDF uploaded?) | 50.0% (40/80) | 0.0% (0/20) | 40.0% (40/100) |
| Always document | 50.0% (40/80) | 0.0% (0/20) | 40.0% (40/100) |
| Always topic | 50.0% (40/80) | 0.0% (0/20) | 40.0% (40/100) |

Similarity fallback used on 0 of 100 questions.

### Confusion matrix (rows = expected, columns = predicted)

| Expected \ Predicted | document | topic | mixed |
|---|---|---|---|
| document | 36 | 0 | 4 |
| topic | 0 | 38 | 2 |
| mixed | 0 | 0 | 20 |

## Latency (seconds)

| Stage | n | Median | 90th percentile |
|---|---|---|---|
| ingest | 2 | 10.60 | 17.41 |
| route | 100 | 4.73 | 6.37 |
| retrieve | 62 | 0.02 | 0.03 |
| generate | 100 | 96.09 | 275.73 |
| summarize | 100 | 44.82 | 59.19 |
| tts | 100 | 0.94 | 1.83 |
| total | 100 | 135.38 | 325.30 |

`total` = query to finished answer (route, retrieve, generate, summarize, tts); `ingest` is counted once per document.

## LLM-judge scores

Judge prompt: `judge_prompt.txt`. Spot-check a sample by hand (`spot_check.csv`) before reporting these.

| Measure | Result |
|---|---|
| Faithfulness: yes | 42 of 61 (68.9%) |
| Faithfulness: partial | 10 of 61 (16.4%) |
| Faithfulness: no | 9 of 61 (14.8%) |
| Relevance (1-5), mean | 4.54 over 93 answers |

Judge replies that could not be parsed: 7.
