from agent import rule_intent

# groq $/1M tokens (rough, for display only)
RATES = {
    "text_in": 0.59,
    "text_out": 0.79,
    "vision_in": 0.18,
    "vision_out": 0.18,
    "whisper_min": 0.006,
}

OUT_EST = 400


def tokens(n: int | str) -> int:
    if isinstance(n, str):
        return max(1, len(n) // 4)
    return max(1, n // 4)


def guess_intent(query: str, types: list[str]) -> str | None:
    ruled = rule_intent(query, types, [])
    if ruled:
        return ruled
    if query.strip():
        return "ans_ques"
    return None


def guess_tools(intent: str | None, types: list[str], query: str = "") -> list[str]:
    if not intent:
        return []

    tools = []
    if "image" in types:
        tools.append("ocr")
    if "pdf" in types:
        tools.append("pdf")
    if "audio" in types:
        tools.append("transcribe")

    if intent == "fetch_youtube":
        tools += ["find_url", "fetch_youtube"]
        return tools
    if intent == "summarize":
        return tools + ["summarize"]
    if intent == "compare":
        return tools + ["compare"]
    if intent == "explain_code":
        return tools + ["explain_code"]
    if intent == "sentiment":
        return tools + ["sentiment"]

    if not rule_intent(query, types, []):
        tools.append("classify")
    tools.append("ans_ques")
    return tools


def file_tokens(meta: list[dict]) -> tuple[int, float]:
    ctx = 0
    extra = 0.0

    for f in meta:
        size = f.get("size", 0)
        name = (f.get("name") or "").lower()
        mime = f.get("type") or ""

        if mime == "application/pdf" or name.endswith(".pdf"):
            ctx += min(size // 40, 12000)
        elif mime.startswith("image/") or name.endswith((".jpg", ".jpeg", ".png")):
            ctx += 800
            extra += (tokens(800) * RATES["vision_in"] + tokens(300) * RATES["vision_out"]) / 1_000_000
        elif mime.startswith("audio/") or name.endswith((".mp3", ".wav", ".m4a")):
            mins = max(0.5, size / (1024 * 1024))
            ctx += int(mins * 900)
            extra += mins * RATES["whisper_min"]

    return ctx, extra


def estimate(query: str, types: list[str], meta: list[dict] | None = None) -> dict:
    meta = meta or []
    intent = guess_intent(query, types)
    tools = guess_tools(intent, types, query)

    ctx_tok, ingest_cost = file_tokens(meta)
    query_tok = tokens(query)
    llm_in = query_tok + ctx_tok + 120

    llm_calls = 0
    if intent in {"summarize", "ans_ques", "sentiment", "explain_code", "compare"}:
        llm_calls = 1
    if "classify" in tools:
        llm_calls += 1
    if intent == "fetch_youtube" and query and any(w in query.lower() for w in ["summarize", "summary", "summarise"]):
        llm_calls += 1

    in_tok = llm_in * llm_calls
    out_tok = OUT_EST * llm_calls
    llm_cost = (in_tok * RATES["text_in"] + out_tok * RATES["text_out"]) / 1_000_000
    total = ingest_cost + llm_cost

    return {
        "intent": intent,
        "tools": tools,
        "tokens_in": in_tok + ctx_tok,
        "tokens_out": out_tok,
        "cost_usd": round(total, 4),
        "cost_label": f"~${total:.4f}",
    }
