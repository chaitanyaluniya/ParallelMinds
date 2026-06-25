import re
import time
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled, VideoUnavailable
from youtube_transcript_api.proxies import GenericProxyConfig
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
_IDX = 0


def proxy_list() -> list[str]:
    raw = (os.getenv("YT_PROXY_LIST") or "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in re.split(r"[\n,;]+", raw) if p.strip()]
    return parts


def next_proxy() -> str | None:
    global _IDX
    pool = proxy_list()
    if not pool:
        return None
    out = pool[_IDX % len(pool)]
    _IDX += 1
    return out


def tries() -> list[str | None]:
    pool = proxy_list()
    if not pool:
        return [None]
    out = []
    for _ in range(len(pool)):
        out.append(next_proxy())
    out.append(None)
    return out


def transcript_api(proxy: str | None = None) -> YouTubeTranscriptApi:
    if not proxy:
        return YouTubeTranscriptApi()
    return YouTubeTranscriptApi(proxy_config=GenericProxyConfig(http_url=proxy, https_url=proxy))


def open_url(url: str, timeout: int = 12, headers: dict | None = None, proxy: str | None = None) -> str:
    hdr = headers or {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=hdr)
    try:
        if proxy:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": proxy, "https": proxy}),
            )
            with opener.open(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="ignore")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def ext_yt(url: str) -> dict:
    vid = vid_from(url)
    if not vid:
        return {"text": "", "video_id": None, "error": "Invalid YouTube URL"}
    hit = _CACHE.get(vid)
    if hit and time.time() - hit["ts"] < CACHE_TTL:
        return {"text": hit["text"], "video_id": vid}

    last_error = None
    for px in tries():
        try:
            api = transcript_api(px)
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
            last_error = e

        txt = timedtext(vid, px)
        if txt:
            _CACHE[vid] = {"text": txt, "ts": time.time()}
            return {"text": txt, "video_id": vid}
        txt = watch_pg(vid, px)
        if txt:
            _CACHE[vid] = {"text": txt, "ts": time.time()}
            return {"text": txt, "video_id": vid}
        txt = from_ytdlp(url, px)
        if txt:
            _CACHE[vid] = {"text": txt, "ts": time.time()}
            return {"text": txt, "video_id": vid}

    note = " (try setting YT_PROXY_LIST on server)" if not proxy_list() else ""
    detail = f": {last_error}" if last_error else ""
    return {"text": "", "video_id": vid, "error": f"Transcript fetch failed{detail}{note}"}


def timedtext(vid: str, proxy: str | None = None) -> str:
    params = urllib.parse.urlencode({"v": vid, "lang": "en", "fmt": "srv3"})
    url = f"https://www.youtube.com/api/timedtext?{params}"
    raw = open_url(url, proxy=proxy).strip()
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


def watch_pg(vid: str, proxy: str | None = None) -> str:
    html = open_url(
        f"https://www.youtube.com/watch?v={vid}",
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"},
        proxy=proxy,
    )
    if not html:
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

    raw = open_url(picked, proxy=proxy).strip()
    if not raw:
        return ""
    return prscap_xml(raw)


def prscap_xml(raw: str) -> str:
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


def from_ytdlp(url: str, proxy: str | None = None) -> str:
    if YoutubeDL is None:
        return ""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    if proxy:
        opts["proxy"] = proxy
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        return ""

    subs = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}
    tracks = pick_tracks(subs) + pick_tracks(auto)
    for u in tracks:
        txt = pull_track(u, proxy)
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


def pull_track(url: str, proxy: str | None = None) -> str:
    raw = open_url(url, proxy=proxy).strip()
    if not raw:
        return ""
    if raw.startswith("WEBVTT"):
        return parse_vtt(raw)
    if raw.startswith("{"):
        return parse_json3(raw)
    return prscap_xml(raw)


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
