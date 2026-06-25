import json
import re

from llm import vision

FORMATS = {"image/jpeg", "image/png", "image/jpg", "image/webp"}


def guess_mime(data: bytes, name: str, mime: str) -> str:
    if mime in FORMATS:
        return "image/jpeg" if mime == "image/jpg" else mime
    low = (name or "").lower()
    if low.endswith(".png"):
        return "image/png"
    if low.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if low.endswith(".webp"):
        return "image/webp"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:2] == b"\xff\xd8":
        return "image/jpeg"
    return mime if mime.startswith("image/") else "image/jpeg"


def ext_img(data: bytes, mime: str, name: str = "") -> dict:
    if not data:
        return {"text": "", "confidence": "none", "error": "Empty image data"}

    mime = guess_mime(data, name, mime)
    if mime not in FORMATS:
        return {"text": "", "confidence": "none", "error": f"Unsupported image type: {mime}"}

    prompt = "Extract all visible text from this image. Return only the text, keep line breaks."
    out = vision(prompt, data, mime)
    if out.get("error"):
        return {"text": "", "confidence": "none", "error": out["error"]}
    return parse_res(out["text"])


def parse_res(raw: str) -> dict:
    cleaned = raw.strip()
    if not cleaned:
        return {"text": "", "confidence": "none", "error": "OCR returned nothing"}

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    if cleaned.startswith("{"):
        try:
            parsed = json.loads(cleaned)
            txt = (parsed.get("text") or "").strip()
            conf = parsed.get("confidence", "medium")
            if conf not in {"high", "medium", "low"}:
                conf = "medium"
            if txt:
                return {"text": txt, "confidence": conf}
        except json.JSONDecodeError:
            pass

    return {"text": cleaned, "confidence": "medium"}
