import os
import tempfile

from llm import transcribe

AUDIO = {".mp3", ".wav", ".m4a"}


def ext_audio(data: bytes, name: str) -> dict:
    if not data:
        return {"text": "", "duration": None, "error": "Empty audio data"}

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
        return {"text": out.get("text", ""), "duration": out.get("duration")}
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
