"""Text-to-speech with pyttsx3 (offline).

In-process pyttsx3 + Streamlit reruns often breaks Windows SAPI5/COM after the
first utterance, so every call runs pyttsx3 in a short-lived subprocess.

synthesize_to_wav() writes a WAV the browser can play (st.audio).
speak() keeps the April 2026 behaviour: speech on the host's speakers.
"""
import os
import subprocess
import sys
import tempfile

import config

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

# Text goes through stdin as UTF-8 bytes; the Windows default code page (cp1252)
# can't encode characters such as β or ₁ that answers often contain.
_SPEAK_CODE = r"""import pyttsx3, sys
_t = sys.stdin.buffer.read().decode("utf-8")
if _t.strip():
    _e = pyttsx3.init()
    try:
        _e.say(_t)
        _e.runAndWait()
    finally:
        try:
            _e.stop()
        except Exception:
            pass
"""

_SAVE_CODE = r"""import pyttsx3, sys
_out = sys.argv[1]
_t = sys.stdin.buffer.read().decode("utf-8")
_e = pyttsx3.init()
try:
    _e.save_to_file(_t, _out)
    _e.runAndWait()
finally:
    try:
        _e.stop()
    except Exception:
        pass
"""


def _clip(text):
    text = str(text or "")
    if len(text) > config.TTS_MAX_CHARS:
        text = text[: config.TTS_MAX_CHARS] + "..."
    return text


def speak(text):
    """Speak on the host machine (old behaviour)."""
    text = _clip(text)
    if not text.strip():
        return
    try:
        subprocess.run([sys.executable, "-c", _SPEAK_CODE],
                       input=text.encode("utf-8"), timeout=600,
                       creationflags=_NO_WINDOW)
    except subprocess.TimeoutExpired:
        pass


def synthesize_to_wav(text, out_path=None):
    """Write speech for `text` to a WAV file and return its path, or None."""
    text = _clip(text)
    if not text.strip():
        return None
    if out_path is None:
        fd, out_path = tempfile.mkstemp(suffix=".wav", prefix="avt_tts_")
        os.close(fd)
    try:
        subprocess.run([sys.executable, "-c", _SAVE_CODE, out_path],
                       input=text.encode("utf-8"), timeout=600,
                       creationflags=_NO_WINDOW)
    except subprocess.TimeoutExpired:
        return None
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return out_path
    return None
