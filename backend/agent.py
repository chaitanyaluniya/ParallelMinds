import json
import os
import re

from format import fmt_summary, strip_md
from llm import stream, text

from tools.code import code_prompt, looks_like_code
from tools.compare import cmp_prompt
from tools.sentiment import sent_prompt
from tools.summarizer import qa_prompt, sum_prompt
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
    out = {}
    for ev in run_live(query, types, extracted):
        if ev["type"] == "plan":
            out["plan"] = ev["plan"]
        elif ev["type"] == "token":
            out["answer"] = out.get("answer", "") + ev["text"]
        elif ev["type"] == "done":
            out.update(ev)
            break
    return {
        "need_clr": out.get("need_clr", False),
        "question": out.get("question"),
        "answer": out.get("answer", ""),
        "intent": out.get("intent"),
        "plan": out.get("plan", []),
        "extracted": out.get("extracted", []),
    }


def run_live(query: str, types: list[str], extracted: list[dict] | None = None):
    extracted = extracted or []
    result = cls_intent(query, types, extracted)

    if result.get("error"):
        yield done(fail_clr(result["error"], extracted))
        return

    if result.get("need_clr"):
        yield done({
            "need_clr": True,
            "question": result.get("question") or "Could you clarify what you'd like me to do?",
            "answer": "",
            "intent": result.get("intent"),
            "plan": [],
            "extracted": extracted,
        })
        return

    intent = result["intent"]
    ctx = content(extracted, query)

    if intent == "summarize":
        yield from live_summarize(query, ctx, extracted)
        return

    if intent == "ans_ques":
        yield from live_one("ans_ques", intent, qa_prompt(ctx, query), extracted)
        return

    if intent == "sentiment":
        yield from live_one("sentiment", intent, sent_prompt(ctx), extracted)
        return

    if intent == "explain_code":
        yield from live_one("explain_code", intent, code_prompt(code_ctx(extracted, query), query), extracted, strip_md)
        return

    if intent == "compare":
        if len(extracted) < 2:
            yield done(ok("Need at least 2 inputs to compare", intent, [], extracted))
            return
        yield from live_one("compare", intent, cmp_prompt(ctx, query), extracted)
        return

    if intent == "fetch_youtube":
        yield from live_youtube(query, extracted)
        return

    yield done(ok("", intent, [], extracted))


def live_one(tool: str, intent: str, prompt: str, extracted: list[dict], fmt=None):
    plan = [{"step": 1, "tool": tool, "status": "running"}]
    yield plan_ev(plan)

    text_out, err = yield from stream_llm(prompt, fmt)
    plan[0]["status"] = "failed" if err else "done"
    yield plan_ev(plan)
    yield done(ok(text_out if not err else err, intent, plan, extracted))


def live_summarize(query: str, ctx: str, extracted: list[dict]):
    plan = []
    step = 1
    for item in extracted:
        if item.get("type") == "audio" and item.get("text"):
            plan.append({"step": step, "tool": "transcribe", "status": "done"})
            step += 1
            break

    plan.append({"step": step, "tool": "summarize", "status": "running"})
    yield plan_ev(plan)

    text_out, err = yield from stream_llm(sum_prompt(ctx, query), fmt_summary)
    plan[-1]["status"] = "failed" if err else "done"
    yield plan_ev(plan)
    yield done(ok(text_out if not err else err, "summarize", plan, extracted))


def live_youtube(query: str, extracted: list[dict]):
    ctx = content(extracted, query)
    urls = find_urls(f"{query}\n{ctx}")
    if not urls:
        plan = [{"step": 1, "tool": "find_url", "status": "failed"}]
        yield plan_ev(plan)
        yield done(ok("No YouTube URL found in the inputs", "fetch_youtube", plan, extracted))
        return

    plan = [
        {"step": 1, "tool": "find_url", "status": "done"},
        {"step": 2, "tool": "fetch_youtube", "status": "running"},
    ]
    yield plan_ev(plan)

    yt = ext_yt(urls[0])
    if yt.get("error"):
        plan[1]["status"] = "failed"
        yield plan_ev(plan)
        yield done(ok(yt["error"], "fetch_youtube", plan, extracted))
        return

    plan[1]["status"] = "done"
    yield plan_ev(plan)

    if re.search(r"summarize|summary|summarise", query, re.I):
        plan.append({"step": 3, "tool": "summarize", "status": "running"})
        yield plan_ev(plan)

        text_out, err = yield from stream_llm(sum_prompt(yt["text"], query), fmt_summary)
        plan[2]["status"] = "failed" if err else "done"
        yield plan_ev(plan)
        yield done(ok(text_out if not err else err, "fetch_youtube", plan, extracted))
        return

    yield {"type": "token", "text": yt["text"]}
    yield done(ok(yt["text"], "fetch_youtube", plan, extracted))


def plan_ev(plan: list) -> dict:
    return {"type": "plan", "plan": [dict(s) for s in plan]}


def stream_llm(prompt: str, fmt=None):
    parts = []
    for chunk in stream(prompt):
        if isinstance(chunk, dict) and chunk.get("error"):
            return (chunk["error"], chunk["error"])
        parts.append(chunk)
        yield {"type": "token", "text": chunk}
    raw = "".join(parts).strip()
    if not raw:
        return ("Empty LLM response", "Empty LLM response")
    out = fmt(raw) if fmt else raw
    return (out, None)


def done(payload: dict) -> dict:
    return {"type": "done", **payload}


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
