"""Speech-to-text with faster-whisper, loaded only when first used."""
import os
import tempfile

import config

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(config.WHISPER_MODEL, device=config.WHISPER_DEVICE,
                              compute_type=config.WHISPER_COMPUTE_TYPE)
    return _model


def transcribe(audio_bytes, suffix=".wav"):
    """Return the transcript of recorded audio bytes ('' if none)."""
    if not audio_bytes:
        return ""
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="avt_stt_")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(audio_bytes)
        segments, _info = _get_model().transcribe(path)
        return " ".join(s.text.strip() for s in segments).strip()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
