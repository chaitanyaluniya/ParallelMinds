import base64
import os

from groq import APIError, Groq


def _client() -> Groq | None:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return Groq(api_key=key)


def text(prompt: str) -> dict:
    client = _client()
    if not client:
        return {"text": "", "error": "GROQ_API_KEY not set"}
    try:
        res = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        out = res.choices[0].message.content
        if not out:
            return {"text": "", "error": "Empty LLM response"}
        return {"text": out.strip()}
    except APIError as e:
        return {"text": "", "error": f"LLM failed: {e}"}


def vision(prompt: str, data: bytes, mime: str) -> dict:
    client = _client()
    if not client:
        return {"text": "", "error": "GROQ_API_KEY not set"}
    b64 = base64.b64encode(data).decode()
    try:
        res = client.chat.completions.create(
            model=os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview"),
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            }],
            temperature=0.1,
        )
        out = res.choices[0].message.content
        if not out:
            return {"text": "", "error": "Empty vision response"}
        return {"text": out.strip()}
    except APIError as e:
        return {"text": "", "error": f"Vision failed: {e}"}


def transcribe(path: str) -> dict:
    client = _client()
    if not client:
        return {"text": "", "error": "GROQ_API_KEY not set"}
    try:
        with open(path, "rb") as f:
            res = client.audio.transcriptions.create(
                file=(os.path.basename(path), f.read()),
                model=os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3"),
                response_format="verbose_json",
            )
        text_out = res.text.strip() if res.text else ""
        duration = getattr(res, "duration", None)
        return {"text": text_out, "duration": duration}
    except APIError as e:
        return {"text": "", "error": f"Transcription failed: {e}"}
    except OSError as e:
        return {"text": "", "error": f"Audio read failed: {e}"}
