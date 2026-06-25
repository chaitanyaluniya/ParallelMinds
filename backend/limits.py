import os

MAX_FILE = int(os.getenv("MAX_FILE_MB", "25")) * 1024 * 1024  # ~5–10 min mp3
MAX_AUDIO = int(os.getenv("MAX_AUDIO_MB", "25")) * 1024 * 1024
MAX_AUDIO_SEC = int(os.getenv("MAX_AUDIO_SEC", "600"))  # 10 min cap
MAX_CTX = int(os.getenv("MAX_CTX_TOKENS", "12000"))

RATES = {
    "text_in": 0.59,
    "text_out": 0.79,
    "vision_in": 0.18,
    "vision_out": 0.18,
    "whisper_min": 0.006,
}


def tokens(text: str) -> int:
    return max(1, len(text) // 4)


SUFFIX = "\n[truncated — context too long]"


def trim(text: str, max_tok: int) -> tuple[str, bool]:
    if tokens(text) <= max_tok:
        return text, False
    room = max(1, max_tok - tokens(SUFFIX))
    cap = room * 4
    cut = text[:cap].rsplit(" ", 1)[0] or text[:cap]
    return cut.rstrip() + SUFFIX, True


def price(in_tok: int, out_tok: int, vision_in=0, vision_out=0, whisper_min=0.0) -> float:
    llm = (in_tok * RATES["text_in"] + out_tok * RATES["text_out"]) / 1_000_000
    vis = (vision_in * RATES["vision_in"] + vision_out * RATES["vision_out"]) / 1_000_000
    aud = whisper_min * RATES["whisper_min"]
    return round(llm + vis + aud, 6)
