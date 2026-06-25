import json
import os
import re

from llm import text

from tools.code import explain, looks_like_code
from tools.compare import compare
from tools.sentiment import sentiment
from tools.summarizer import answer, summarize
from tools.youtube import ext_yt, find_urls

INTENTS = {
    "summarize",
    "ans_ques",
    "sentiment",
    "explain_code",
    "compare",
    "fetch_youtube",
}

PROMPT = """Classify intent from the query and input types.
JSON only: {{"intent":"...","need_clr":false,"question":null}}

Intents:
- summarize — wants summary (1-line, bullets, paragraph)
- ans_ques — general Q&A about the content
- sentiment — sentiment label + justification
- explain_code — explain code, find bugs, mention complexity
- compare — compare content across multiple inputs
- fetch_youtube — fetch transcript or summarize a YouTube URL in the content

need_clr=true if task is unclear, vague (e.g. "do something with this"), or multiple intents fit equally.
If true, question must be one short follow-up.

Query: {query}
Input types: {types}
"""


def run(query: str, types: list[str], extracted: list[dict] | None = None) -> dict:
    extracted = extracted or []
    result = cls_intent(query, types, extracted)

    if result.get("error"):
        return fail_clr(result["error"], extracted)

    if result.get("need_clr"):
        return {
            "need_clr": True,
            "question": result.get("question") or "Could you clarify what you'd like me to do?",
            "answer": "",
            "intent": result.get("intent"),
            "plan": [],
            "extracted": extracted,
        }

    intent = result["intent"]
    ctx = content(extracted, query)

    if intent == "summarize":
        return do_summarize(query, ctx, extracted)

    if intent == "ans_ques":
        plan = [{"step": 1, "tool": "ans_ques", "status": "running"}]
        out = answer(ctx, query)
        plan[0]["status"] = "failed" if out.get("error") else "done"
        return ok(out.get("text", "") if not out.get("error") else out["error"], intent, plan, extracted)

    if intent == "sentiment":
        plan = [{"step": 1, "tool": "sentiment", "status": "running"}]
        out = sentiment(ctx)
        plan[0]["status"] = "failed" if out.get("error") else "done"
        return ok(out.get("text", "") if not out.get("error") else out["error"], intent, plan, extracted)

    if intent == "explain_code":
        plan = [{"step": 1, "tool": "explain_code", "status": "running"}]
        out = explain(code_ctx(extracted, query), query)
        plan[0]["status"] = "failed" if out.get("error") else "done"
        return ok(out.get("text", "") if not out.get("error") else out["error"], intent, plan, extracted)

    if intent == "compare":
        if len(extracted) < 2:
            return ok("Need at least 2 inputs to compare", intent, [], extracted)
        plan = [{"step": 1, "tool": "compare", "status": "running"}]
        out = compare(ctx, query)
        plan[0]["status"] = "failed" if out.get("error") else "done"
        return ok(out.get("text", "") if not out.get("error") else out["error"], intent, plan, extracted)

    if intent == "fetch_youtube":
        return do_youtube(query, extracted)

    return ok("", intent, [], extracted)


def cls_intent(query: str, types: list[str], extracted: list[dict]) -> dict:
    if not query.strip() and not types:
        return {"intent": None, "need_clr": True, "question": "What would you like me to do?"}

    if not query.strip() and types:
        return {"intent": None, "need_clr": True, "question": "What do you want me to do with these files?"}

    ruled = rule_intent(query, types, extracted)
    if ruled:
        return {"intent": ruled, "need_clr": False, "question": None}

    if not os.getenv("GROQ_API_KEY"):
        return {"intent": None, "need_clr": True, "question": None, "error": "GROQ_API_KEY not set"}

    out = text(PROMPT.format(query=query.strip(), types=", ".join(types) or "none"))
    if out.get("error"):
        return {"intent": None, "need_clr": True, "question": None, "error": f"Classification failed: {out['error']}"}
    if not out.get("text"):
        return {"intent": None, "need_clr": True, "question": None, "error": "Empty LLM response"}
    return prs_intent(out["text"])


def rule_intent(query: str, types: list[str], extracted: list[dict]) -> str | None:
    q = query.lower()
    combined = f"{query}\n{build_ctx(extracted)}"

    if find_urls(combined):
        return "fetch_youtube"

    if looks_like_code(query) or ("explain" in q and ("image" in types or looks_like_code(query))):
        return "explain_code"

    if any(w in q for w in ["sentiment", "positive or negative", "feel about", "tone of"]):
        return "sentiment"

    if len(extracted) >= 2 and any(w in q for w in ["compare", "same topic", "both discuss", "difference between"]):
        return "compare"

    if any(w in q for w in ["summarize", "summary", "summarise", "tl;dr", "key points"]):
        return "summarize"

    if any(w in q for w in ["action item", "what are the", "extract", "find the"]):
        return "ans_ques"

    return None


def do_summarize(query: str, ctx: str, extracted: list[dict]) -> dict:
    plan = []
    step = 1
    for item in extracted:
        if item.get("type") == "audio" and item.get("text"):
            plan.append({"step": step, "tool": "transcribe", "status": "done"})
            step += 1
            break

    plan.append({"step": step, "tool": "summarize", "status": "running"})
    out = summarize(ctx, query)
    plan[-1]["status"] = "failed" if out.get("error") else "done"
    return ok(out.get("text", "") if not out.get("error") else out["error"], "summarize", plan, extracted)


def do_youtube(query: str, extracted: list[dict]) -> dict:
    ctx = content(extracted, query)
    urls = find_urls(f"{query}\n{ctx}")
    if not urls:
        return ok("No YouTube URL found in the inputs", "fetch_youtube", [{"step": 1, "tool": "find_url", "status": "failed"}], extracted)

    plan = [
        {"step": 1, "tool": "find_url", "status": "done"},
        {"step": 2, "tool": "fetch_youtube", "status": "running"},
    ]
    yt = ext_yt(urls[0])
    if yt.get("error"):
        plan[1]["status"] = "failed"
        return ok(yt["error"], "fetch_youtube", plan, extracted)

    plan[1]["status"] = "done"
    if re.search(r"summarize|summary|summarise", query, re.I):
        plan.append({"step": 3, "tool": "summarize", "status": "running"})
        out = summarize(yt["text"], query)
        plan[2]["status"] = "failed" if out.get("error") else "done"
        return ok(out.get("text", "") if not out.get("error") else out["error"], "fetch_youtube", plan, extracted)

    return ok(yt["text"], "fetch_youtube", plan, extracted)


def content(extracted: list[dict], query: str) -> str:
    ctx = build_ctx(extracted)
    return ctx if ctx.strip() else query.strip()


def code_ctx(extracted: list[dict], query: str) -> str:
    ctx = build_ctx(extracted)
    if ctx.strip():
        return ctx
    return query


def build_ctx(extracted: list[dict]) -> str:
    parts = []
    for item in extracted:
        label = item.get("name") or item.get("type") or "input"
        text = item.get("text", "").strip()
        if text:
            line = f"[{label}]\n{text}"
            if item.get("confidence"):
                line += f"\n(OCR confidence: {item['confidence']})"
            parts.append(line)
    return "\n\n".join(parts)


def ok(answer: str, intent: str, plan: list, extracted: list[dict]) -> dict:
    return {
        "need_clr": False,
        "question": None,
        "answer": answer,
        "intent": intent,
        "plan": plan,
        "extracted": extracted,
    }


def fail_clr(msg: str, extracted: list[dict]) -> dict:
    return {
        "need_clr": True,
        "question": msg,
        "answer": "",
        "intent": None,
        "plan": [],
        "extracted": extracted,
    }


def prs_intent(raw: str) -> dict:
    cleaned = raw
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
        intent = data.get("intent")
        if intent not in INTENTS:
            intent = "ans_ques"
        return {
            "intent": intent,
            "need_clr": bool(data.get("need_clr")),
            "question": data.get("question"),
        }
    except json.JSONDecodeError:
        return {"intent": "ans_ques", "need_clr": False, "question": None}
