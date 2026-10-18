# Agentic Voice Tutor (v2)

A multi-agent study assistant. It answers questions from a learner's own PDF,
from general knowledge, or from both, and replies with an explanation, study
notes and speech.

## Setup

1. Install Python 3.10 or newer, then the dependencies:

   ```
   pip install -r agentic_voice_tutor/requirements.txt
   ```

2. Install [Ollama](https://ollama.com), then download the model and keep Ollama running:

   ```
   ollama pull llama3
   ```

3. Run the app:

   ```
   cd agentic_voice_tutor
   streamlit run app.py
   ```

The first voice question downloads the Whisper "base" model (about 150 MB);
the first document downloads the all-MiniLM-L6-v2 embedding model.

Settings live in `agentic_voice_tutor/config.py`. Each one can be overridden
with an environment variable, for example `AVT_TOP_K=5` or `AVT_TTS_MODE=host`.

## How a question is answered

1. **Input.** Type the question, or record it; voice is transcribed with faster-whisper.
2. **Coordination agent** (`agents/router_agent.py`). With no document loaded the
   query goes to Topic mode without an LLM call. Otherwise Llama 3 classifies it
   as `document`, `topic` or `mixed` from a few-shot prompt that must return JSON.
   If the reply can't be parsed, the agent falls back to the best FAISS similarity
   between the query and the document (thresholds in `config.py`).
3. **Document mode.** The PDF is parsed with pypdf, split into 500-word chunks with
   a 50-word overlap, embedded with all-MiniLM-L6-v2 and indexed in FAISS once per
   file. The top 3 chunks go to the document agent, which answers only from them.
4. **Topic mode.** The topic knowledge agent answers from the language model with
   a tutoring system prompt.
5. **Mixed mode.** Both agents answer, and a merge agent combines the two,
   marking what comes from the document.
6. **Notes agent** writes 3 to 6 bullet-point study notes.
7. **Voice output.** pyttsx3 writes a WAV that plays in the browser.

Expand "How this answer was produced" under an answer to see the route, the
retrieved chunks with their similarity scores and the time each stage took.

## What changed from the April 2026 prototype

| Area | April 2026 prototype | v2 |
|---|---|---|
| Routing | Document mode whenever a PDF was uploaded, otherwise Topic mode | LLM intent classifier (document / topic / mixed) with a similarity fallback; the old rule is kept as an evaluation baseline |
| Agents | One tutor prompt for both modes | Separate document, topic, merge and notes agents |
| Mixed questions | Not supported | Both agents answer, then a merge agent combines them |
| Indexing | Whole PDF re-parsed and re-indexed on every question | One FAISS index per file, cached by SHA-256 of its bytes |
| Chunking | 500 words, no overlap | 500 words, 50-word overlap (configurable) |
| Retrieval | Top 3 chunks, L2 distance, no scores shown | Top 3 chunks, cosine similarity, scores shown and logged |
| Voice input | None (text box only) | Recorded audio transcribed with faster-whisper |
| Voice output | pyttsx3 on the server's speakers | pyttsx3 to a WAV played in the browser (`AVT_TTS_MODE=host` restores the old behaviour) |
| Observability | None | Per-stage timings and route decision shown in the app and logged by the evaluation |
| Settings | Hard-coded | `config.py` with environment overrides |

Still not included: conversation memory across questions, and any LangChain
components.

## Tests and evaluation

```
pip install pytest reportlab
python -m pytest tests
```

The tests use `AVT_LLM=mock` and `AVT_EMBED=hash`, so they need neither Ollama
nor model downloads. Their outputs are not real model answers.

To measure the system on your own questions, see `eval/README.md`.
