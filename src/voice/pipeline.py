"""Optional faster-whisper STT -> shared runtime -> Piper TTS pipeline."""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
import subprocess
import tempfile

from src.runtime.engine import runtime
from src.shared.models import SessionState


def transcribe_audio(audio_path: str, language: str = "en") -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Install requirements-optional.txt to enable faster-whisper STT.") from exc
    model = _whisper_model(WhisperModel)
    segments, _ = model.transcribe(audio_path, language=language, vad_filter=True)
    return " ".join(segment.text.strip() for segment in segments).strip()


@lru_cache(maxsize=1)
def _whisper_model(model_class):
    return model_class(os.getenv("WHISPER_MODEL", "small"), device=os.getenv("WHISPER_DEVICE", "cpu"), compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"))


def synthesize_speech(text: str, language: str = "en") -> dict[str, str]:
    model = os.getenv("PIPER_MODEL", "")
    if not model:
        return {"engine": "local-tts-stub", "language": language, "text": text}
    output = Path(tempfile.gettempdir()) / "ecombot-voice" / f"response-{language}.wav"
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["piper", "--model", model, "--output_file", str(output)],
        input=text,
        text=True,
        check=True,
        capture_output=True,
    )
    return {"engine": "piper", "language": language, "text": text, "audio_path": str(output)}


def handle_voice_text(transcript: str, state: SessionState | None = None, language: str = "en") -> dict:
    state = state or SessionState(session_id=f"voice-{language}")
    response = runtime.handle(transcript, state)
    return {"transcript": transcript, "response_text": response.text, "tts": synthesize_speech(response.text, language)}
