import re

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
        try:
            snippets = YouTubeTranscriptApi.get_transcript(vid, languages=["en", "en-US", "en-GB"])
        except NoTranscriptFound:
            snippets = YouTubeTranscriptApi.get_transcript(vid)
        text = " ".join(s["text"] for s in snippets).strip()
        return {"text": text, "video_id": vid}
    except TranscriptsDisabled:
        return {"text": "", "video_id": vid, "error": "Captions disabled for this video"}
    except NoTranscriptFound:
        return {"text": "", "video_id": vid, "error": "No transcript available"}
    except VideoUnavailable:
        return {"text": "", "video_id": vid, "error": "Video unavailable"}
    except Exception as e:
        return {"text": "", "video_id": vid, "error": f"Transcript fetch failed: {e}"}


def vid_from(url: str) -> str | None:
    url = url.strip()
    if re.fullmatch(r"[\w-]{11}", url):
        return url
    match = PATTERN.search(url)
    return match.group(1) if match else None
