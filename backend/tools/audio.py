import os
import tempfile

from limits import MAX_AUDIO, MAX_AUDIO_SEC
from llm import transcribe

AUDIO = {".mp3", ".wav", ".m4a"}


def ext_audio(data: bytes, name: str) -> dict:
    if not data:
        return {"text": "", "duration": None, "error": "Empty audio data"}

    if len(data) > MAX_AUDIO:
        mb = MAX_AUDIO // (1024 * 1024)
        return {"text": "", "duration": None, "error": f"Audio too large (max {mb}MB)"}

    ext = os.path.splitext(name or "")[1].lower()
    if ext not in AUDIO:
        return {"text": "", "duration": None, "error": f"Unsupported audio type: {ext or 'unknown'}"}

    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(data)
            tmp = f.name
        out = transcribe(tmp)
        if out.get("error"):
            return {"text": "", "duration": None, "error": out["error"]}
        dur = out.get("duration")
        if dur and float(dur) > MAX_AUDIO_SEC:
            return {"text": "", "duration": dur, "error": f"Audio too long (max {MAX_AUDIO_SEC // 60} min)"}
        return {"text": out.get("text", ""), "duration": dur}
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
