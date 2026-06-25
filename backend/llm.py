import base64
import os
import time

from groq import APIError, Groq

from limits import price

RETRIES = 3
WAIT = (1, 2, 4)

_in = 0
_out = 0
_whisper_min = 0.0
_vision_in = 0
_vision_out = 0


def reset():
    global _in, _out, _whisper_min, _vision_in, _vision_out
    _in = _out = _vision_in = _vision_out = 0
    _whisper_min = 0.0


def snap() -> dict:
    cost = price(_in, _out, _vision_in, _vision_out, _whisper_min)
    return {
        "tokens_in": _in + _vision_in,
        "tokens_out": _out + _vision_out,
        "cost_usd": cost,
        "cost_label": f"${cost:.4f}",
    }


def track_whisper(duration):
    global _whisper_min
    if duration:
        _whisper_min += float(duration) / 60


def track_vision(in_tok=800, out_tok=200):
    global _vision_in, _vision_out
    _vision_in += in_tok
    _vision_out += out_tok


def _add(usage):
    global _in, _out
    if not usage:
        return
    _in += getattr(usage, "prompt_tokens", 0) or 0
    _out += getattr(usage, "completion_tokens", 0) or 0


def _client() -> Groq | None:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return Groq(api_key=key)


def _model() -> str:
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _vision_model() -> str:
    return os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")


def _call(fn):
    last = None
    for i in range(RETRIES):
        try:
            return fn()
        except APIError as e:
            last = e
            code = getattr(e, "status_code", None)
            if code != 429 or i == RETRIES - 1:
                raise
            time.sleep(WAIT[min(i, len(WAIT) - 1)])
    raise last


def text(prompt: str) -> dict:
    client = _client()
    if not client:
        return {"text": "", "error": "GROQ_API_KEY not set"}
    try:
        res = _call(lambda: client.chat.completions.create(
            model=_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        ))
        _add(res.usage)
        out = res.choices[0].message.content
        if not out:
            return {"text": "", "error": "Empty LLM response"}
        return {"text": out.strip()}
    except APIError as e:
        return {"text": "", "error": f"LLM failed: {e}"}


def stream(prompt: str):
    client = _client()
    if not client:
        yield {"error": "GROQ_API_KEY not set"}
        return
    try:
        res = _call(lambda: client.chat.completions.create(
            model=_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            stream=True,
        ))
        parts = []
        got_usage = False
        for chunk in res:
            if getattr(chunk, "usage", None):
                _add(chunk.usage)
                got_usage = True
            part = chunk.choices[0].delta.content
            if part:
                parts.append(part)
                yield part
        if parts and not got_usage:
            global _in, _out
            _in += max(1, len(prompt) // 4)
            _out += max(1, len("".join(parts)) // 4)
    except APIError as e:
        yield {"error": f"LLM failed: {e}"}


def ask(prompt: str, on_chunk=None) -> dict:
    if not on_chunk:
        return text(prompt)

    parts = []
    for chunk in stream(prompt):
        if isinstance(chunk, dict) and chunk.get("error"):
            return {"text": "", "error": chunk["error"]}
        parts.append(chunk)
        on_chunk(chunk)
    out = "".join(parts).strip()
    if not out:
        return {"text": "", "error": "Empty LLM response"}
    return {"text": out}


def vision(prompt: str, data: bytes, mime: str) -> dict:
    client = _client()
    if not client:
        return {"text": "", "error": "GROQ_API_KEY not set"}
    b64 = base64.b64encode(data).decode()
    try:
        res = _call(lambda: client.chat.completions.create(
            model=_vision_model(),
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            }],
            temperature=0.1,
            max_completion_tokens=2048,
        ))
        if res.usage:
            track_vision(res.usage.prompt_tokens, res.usage.completion_tokens)
        else:
            track_vision(800, 200)
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
            res = _call(lambda: client.audio.transcriptions.create(
                file=(os.path.basename(path), f.read()),
                model=os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3"),
                response_format="verbose_json",
            ))
        text_out = res.text.strip() if res.text else ""
        duration = getattr(res, "duration", None)
        track_whisper(duration)
        return {"text": text_out, "duration": duration}
    except APIError as e:
        return {"text": "", "error": f"Transcription failed: {e}"}
    except OSError as e:
        return {"text": "", "error": f"Audio read failed: {e}"}
