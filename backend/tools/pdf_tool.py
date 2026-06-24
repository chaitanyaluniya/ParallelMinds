import io
import re

import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException

PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([\w-]{11})",
    re.IGNORECASE,
)


def ext_pdf(data: bytes) -> dict:
    if not data:
        return {"text": "", "pages": 0, "urls": [], "error": "Empty PDF data"}

    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            parts = [page.extract_text() or "" for page in pdf.pages]
            text = "\n\n".join(parts).strip()
            return {
                "text": text,
                "pages": len(pdf.pages),
                "urls": _find_youtube_urls(text),
            }
    except (ValueError, OSError, PdfminerException) as e:
        return {"text": "", "pages": 0, "urls": [], "error": f"Invalid or corrupted PDF: {e}"}


def youtube_url(text: str) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for match in YOUTUBE_PATTERN.finditer(text):
        video_id = match.group(1)
        if video_id in seen:
            continue
        seen.add(video_id)
        urls.append(f"https://www.youtube.com/watch?v={video_id}")
    return urls
