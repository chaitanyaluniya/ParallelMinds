from agent import rule_intent
from limits import MAX_CTX, RATES, price, tokens, trim

OUT_EST = 400


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
        return tools + ["find_url", "fetch_youtube"]
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
            ctx += min(size // 40, MAX_CTX)
        elif mime.startswith("image/") or name.endswith((".jpg", ".jpeg", ".png")):
            ctx += 800
            extra += price(0, 0, 800, 300)
        elif mime.startswith("audio/") or name.endswith((".mp3", ".wav", ".m4a")):
            mins = max(0.5, size / (1024 * 1024))
            ctx += int(mins * 900)
            extra += mins * RATES["whisper_min"]

    return ctx, extra


def estimate(query: str, types: list[str], meta: list[dict] | None = None, history: str = "") -> dict:
    meta = meta or []
    intent = guess_intent(query, types)
    tools = guess_tools(intent, types, query)

    ctx_tok, ingest_cost = file_tokens(meta)
    hist_tok = tokens(history)
    q_trim, _ = trim(query, MAX_CTX // 4)
    query_tok = tokens(q_trim)
    ctx_cap = min(ctx_tok, MAX_CTX - query_tok - hist_tok - 200)
    llm_in = query_tok + ctx_cap + hist_tok + 120

    llm_calls = 0
    if intent in {"summarize", "ans_ques", "sentiment", "explain_code", "compare"}:
        llm_calls = 1
    if "classify" in tools:
        llm_calls += 1
    if intent == "fetch_youtube" and query and any(w in query.lower() for w in ["summarize", "summary", "summarise"]):
        llm_calls += 1

    in_tok = llm_in * llm_calls
    out_tok = OUT_EST * llm_calls
    total = ingest_cost + price(in_tok, out_tok)

    return {
        "intent": intent,
        "tools": tools,
        "tokens_in": in_tok + ctx_cap,
        "tokens_out": out_tok,
        "cost_usd": round(total, 4),
        "cost_label": f"~${total:.4f}",
        "estimate": True,
    }
