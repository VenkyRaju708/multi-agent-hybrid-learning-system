"""Central settings for the Agentic Voice Tutor.

Every value can be overridden with an environment variable of the same name
prefixed with AVT_ (for example AVT_TOP_K=5).
"""
import os


def _env(name, default, cast=str):
    value = os.environ.get("AVT_" + name)
    if value is None or value == "":
        return default
    if cast is bool:
        return value.strip().lower() in ("1", "true", "yes", "on")
    return cast(value)


# --- Language model -------------------------------------------------------
# "ollama" (default) talks to a local Ollama server; "mock" is for tests only.
LLM_BACKEND = _env("LLM", "ollama")
LLM_MODEL = _env("LLM_MODEL", "llama3")

# --- Embeddings -------------------------------------------------------------
# "sentence-transformers" (default) or "hash" (deterministic, tests only).
EMBED_BACKEND = _env("EMBED", "sentence-transformers")
EMBED_MODEL = _env("EMBED_MODEL", "all-MiniLM-L6-v2")

# --- Ingestion and retrieval -------------------------------------------------
CHUNK_SIZE_WORDS = _env("CHUNK_SIZE_WORDS", 500, int)
CHUNK_OVERLAP_WORDS = _env("CHUNK_OVERLAP_WORDS", 50, int)
TOP_K = _env("TOP_K", 3, int)

# --- Routing -----------------------------------------------------------------
# Used only when the LLM router's reply cannot be parsed. Scores are cosine
# similarities between the query and the best-matching document chunk.
ROUTER_DOC_THRESHOLD = _env("ROUTER_DOC_THRESHOLD", 0.45, float)
ROUTER_MIXED_THRESHOLD = _env("ROUTER_MIXED_THRESHOLD", 0.30, float)

# --- Voice -------------------------------------------------------------------
WHISPER_MODEL = _env("WHISPER_MODEL", "base")
WHISPER_DEVICE = _env("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = _env("WHISPER_COMPUTE_TYPE", "int8")
# "browser" (default): synthesize a WAV and play it in the page with st.audio.
# "host": the April 2026 behaviour, speaking on the server's speakers.
TTS_MODE = _env("TTS_MODE", "browser")
TTS_MAX_CHARS = _env("TTS_MAX_CHARS", 8000, int)
