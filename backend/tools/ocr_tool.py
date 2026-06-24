import json
import os
import re

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

ALLOWED_MIMES = {"image/jpeg", "image/png", "image/jpg"}


def extract_image(data: bytes, mime: str) -> dict:
    if not data:
        return {"text": "", "confidence": "none", "error": "Empty image data"}

    mime = "image/jpeg" if mime == "image/jpg" else mime
    if mime not in ALLOWED_MIMES:
        return {"text": "", "confidence": "none", "error": f"Unsupported image type: {mime}"}

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"text": "", "confidence": "none", "error": "GOOGLE_API_KEY not set"}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
        response = model.generate_content([
            'Extract all visible text. Reply with JSON only: {"text":"...","confidence":"high|medium|low"}',
            {"mime_type": mime, "data": data},
        ])
        if not response.text:
            return {"text": "", "confidence": "none", "error": "Gemini returned empty response"}
        return _parse_response(response.text.strip())
    except (GoogleAPIError, ValueError) as e:
        return {"text": "", "confidence": "none", "error": f"OCR failed: {e}"}


def _parse_response(raw: str) -> dict:
    cleaned = raw
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
        text = parsed.get("text", "")
        confidence = parsed.get("confidence", "medium")
        if confidence not in {"high", "medium", "low"}:
            confidence = "medium"
        return {"text": text.strip(), "confidence": confidence}
    except json.JSONDecodeError:
        return {"text": raw.strip(), "confidence": "medium"}
