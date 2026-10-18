import os
import sys

# Must be set before any app module imports config.
os.environ["AVT_LLM"] = "mock"
os.environ["AVT_EMBED"] = "hash"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "agentic_voice_tutor"))
sys.path.insert(0, os.path.join(ROOT, "eval"))

import pytest  # noqa: E402

SAMPLE_TEXT = (
    "Photosynthesis happens in the chloroplast. The light reactions make ATP and NADPH. "
    "The Calvin cycle fixes carbon dioxide into sugar. " * 40
)


@pytest.fixture(autouse=True)
def _fresh_cache():
    from retrieval.vector_store import clear_cache

    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def sample_doc(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text(SAMPLE_TEXT, encoding="utf-8")
    return path
