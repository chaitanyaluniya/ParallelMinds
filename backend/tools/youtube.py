import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled, VideoUnavailable

PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([\w-]{11})",
    re.IGNORECASE,
)


def ext_yt(url: str) -> dict:
    vid = vid_from(url)
    if not vid:
        return {"text": "", "video_id": None, "error": "Invalid YouTube URL"}

    try:
        api = YouTubeTranscriptApi()
        try:
            t = api.fetch(vid, languages=["en", "en-US", "en-GB"])
        except NoTranscriptFound:
            t = api.fetch(vid)
        text = " ".join(s.text for s in t.snippets).strip()
        return {"text": text, "video_id": vid}
    except TranscriptsDisabled:
        return {"text": "", "video_id": vid, "error": "Captions disabled for this video"}
    except NoTranscriptFound:
        return {"text": "", "video_id": vid, "error": "No transcript available"}
    except VideoUnavailable:
        return {"text": "", "video_id": vid, "error": "Video unavailable"}
    except Exception as e:
        txt = timedtext(vid)
        if txt:
            return {"text": txt, "video_id": vid}
        return {"text": "", "video_id": vid, "error": f"Transcript fetch failed: {e}"}


def timedtext(vid: str) -> str:
    params = urllib.parse.urlencode({"v": vid, "lang": "en", "fmt": "srv3"})
    url = f"https://www.youtube.com/api/timedtext?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            raw = r.read().decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""
    if not raw:
        return ""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return ""
    parts = []
    for node in root.findall(".//text"):
        txt = "".join(node.itertext()).strip()
        if txt:
            parts.append(txt)
    return " ".join(parts).strip()


def find_urls(text: str) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for match in PATTERN.finditer(text):
        vid = match.group(1)
        if vid in seen:
            continue
        seen.add(vid)
        urls.append(f"https://www.youtube.com/watch?v={vid}")
    return urls


def vid_from(url: str) -> str | None:
    url = url.strip()
    if re.fullmatch(r"[\w-]{11}", url):
        return url
    match = PATTERN.search(url)
    return match.group(1) if match else None
