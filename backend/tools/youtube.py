import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled, VideoUnavailable
try:
    from yt_dlp import YoutubeDL
except Exception:
    YoutubeDL = None

PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([\w-]{11})",
    re.IGNORECASE,
)
CACHE_TTL = 3600
_CACHE = {}


def ext_yt(url: str) -> dict:
    vid = vid_from(url)
    if not vid:
        return {"text": "", "video_id": None, "error": "Invalid YouTube URL"}
    hit = _CACHE.get(vid)
    if hit and time.time() - hit["ts"] < CACHE_TTL:
        return {"text": hit["text"], "video_id": vid}

    try:
        api = YouTubeTranscriptApi()
        try:
            t = api.fetch(vid, languages=["en", "en-US", "en-GB"])
        except NoTranscriptFound:
            t = api.fetch(vid)
        text = " ".join(s.text for s in t.snippets).strip()
        if text:
            _CACHE[vid] = {"text": text, "ts": time.time()}
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
            _CACHE[vid] = {"text": txt, "ts": time.time()}
            return {"text": txt, "video_id": vid}
        txt = from_watch_page(vid)
        if txt:
            _CACHE[vid] = {"text": txt, "ts": time.time()}
            return {"text": txt, "video_id": vid}
        txt = from_ytdlp(url)
        if txt:
            _CACHE[vid] = {"text": txt, "ts": time.time()}
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


def from_watch_page(vid: str) -> str:
    req = urllib.request.Request(
        f"https://www.youtube.com/watch?v={vid}",
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"},
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            html = r.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""

    m = re.search(r'"captionTracks":(\[.*?\])', html)
    if not m:
        return ""
    block = m.group(1)
    urls = re.findall(r'"baseUrl":"(.*?)"', block)
    if not urls:
        return ""

    picked = None
    for raw in urls:
        url = unescape(raw.replace("\\u0026", "&").replace("\\/", "/"))
        if "lang=en" in url or "languageCode=en" in url:
            picked = url
            break
    if not picked:
        picked = unescape(urls[0].replace("\\u0026", "&").replace("\\/", "/"))

    try:
        with urllib.request.urlopen(urllib.request.Request(picked, headers={"User-Agent": "Mozilla/5.0"}), timeout=12) as r:
            raw = r.read().decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""
    return parse_caption_xml(raw)


def parse_caption_xml(raw: str) -> str:
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
            parts.append(unescape(txt))
    return " ".join(parts).strip()


def from_ytdlp(url: str) -> str:
    if YoutubeDL is None:
        return ""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        return ""

    subs = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}
    tracks = pick_tracks(subs) + pick_tracks(auto)
    for u in tracks:
        txt = pull_track(u)
        if txt:
            return txt
    return ""


def pick_tracks(pool: dict) -> list[str]:
    urls = []
    langs = ["en", "en-US", "en-GB", "a.en"]
    for lang in langs:
        for t in pool.get(lang, []):
            if t.get("url"):
                urls.append(t["url"])
    if urls:
        return urls
    for items in pool.values():
        for t in items:
            if t.get("url"):
                urls.append(t["url"])
    return urls[:3]


def pull_track(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            raw = r.read().decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""
    if not raw:
        return ""
    if raw.startswith("WEBVTT"):
        return parse_vtt(raw)
    if raw.startswith("{"):
        return parse_json3(raw)
    return parse_caption_xml(raw)


def parse_vtt(raw: str) -> str:
    out = []
    for line in raw.splitlines():
        s = line.strip()
        if not s or s == "WEBVTT" or "-->" in s:
            continue
        if s.isdigit():
            continue
        out.append(s)
    return " ".join(out).strip()


def parse_json3(raw: str) -> str:
    try:
        import json
        data = json.loads(raw)
    except Exception:
        return ""
    out = []
    for ev in data.get("events", []):
        for seg in ev.get("segs", []):
            t = (seg.get("utf8") or "").strip()
            if t:
                out.append(t)
    return " ".join(out).strip()


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
