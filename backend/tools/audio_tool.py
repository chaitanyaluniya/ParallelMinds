import json
import os
import re
import tempfile
import time

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

AUDIO = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
}


def ext_audio(data: bytes, name: str) -> dict:
    if not data:
        return {"text": "", "duration": None, "error": "Empty audio data"}

    ext = os.path.splitext(name or "")[1].lower()
    mime = AUDIO.get(ext)
    if not mime:
        return {"text": "", "duration": None, "error": f"Unsupported audio type: {ext or 'unknown'}"}

    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return {"text": "", "duration": None, "error": "GOOGLE_API_KEY not set"}

    tmp = None
    uploaded = None
    try:
        genai.configure(api_key=key)
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(data)
            tmp = f.name

        uploaded = genai.upload_file(tmp, mime_type=mime)
        while uploaded.state.name == "PROCESSING":
            time.sleep(1)
            uploaded = genai.get_file(uploaded.name)
        if uploaded.state.name != "ACTIVE":
            return {"text": "", "duration": None, "error": f"Audio upload failed: {uploaded.state.name}"}

        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
        res = model.generate_content([
            'Transcribe this audio. Clean filler words lightly. JSON only: {"text":"...","duration":123}',
            uploaded,
        ])
        if not res.text:
            return {"text": "", "duration": None, "error": "Gemini returned empty response"}
        return parse_res(res.text.strip())
    except (GoogleAPIError, ValueError, OSError) as e:
        return {"text": "", "duration": None, "error": f"Transcription failed: {e}"}
    finally:
        if uploaded:
            try:
                genai.delete_file(uploaded.name)
            except GoogleAPIError:
                pass
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


def parse_res(raw: str) -> dict:
    cleaned = raw
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
        text = parsed.get("text", "").strip()
        duration = parsed.get("duration")
        if isinstance(duration, str) and duration.isdigit():
            duration = int(duration)
        return {"text": text, "duration": duration if isinstance(duration, (int, float)) else None}
    except json.JSONDecodeError:
        return {"text": raw.strip(), "duration": None}
