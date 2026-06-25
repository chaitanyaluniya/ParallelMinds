import json
import os
import re

from llm import text

from tools.code import explain
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
- fetch_youtube — fetch/summarize a YouTube URL found in the content

need_clr=true if task is unclear, vague (e.g. "do something with this"), or multiple intents fit equally.
If true, question must be one short follow-up.

Query: {query}
Input types: {types}
"""


def cls_intent(query: str, types: list[str]) -> dict:
    if not query.strip() and not types:
        return {
            "intent": None,
            "need_clr": True,
            "question": "What would you like me to do?",
        }

    if not query.strip() and types:
        return {
            "intent": None,
            "need_clr": True,
            "question": "What do you want me to do with these files?",
        }

    key = os.getenv("GROQ_API_KEY")
    if not key:
        return {"intent": None, "need_clr": True, "question": None, "error": "GROQ_API_KEY not set"}

    out = text(PROMPT.format(query=query.strip(), types=", ".join(types) or "none"))
    if out.get("error"):
        return {"intent": None, "need_clr": True, "question": None, "error": f"Classification failed: {out['error']}"}
    if not out.get("text"):
        return {"intent": None, "need_clr": True, "question": None, "error": "Empty LLM response"}
    return prs_intent(out["text"])


def run(query: str, types: list[str], extracted: list[dict] | None = None) -> dict:
    extracted = extracted or []
    result = cls_intent(query, types)

    if result.get("error"):
        return {
            "need_clr": True,
            "question": result["error"],
            "answer": "",
            "intent": None,
            "plan": [],
            "extracted": extracted,
        }

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
    ctx = build_ctx(extracted)

    if intent == "summarize":
        plan = [{"step": 1, "tool": "summarize", "status": "running"}]
        out = summarize(ctx, query)
        plan[0]["status"] = "failed" if out.get("error") else "done"
        return {
            "need_clr": False,
            "question": None,
            "answer": out.get("text", "") if not out.get("error") else out["error"],
            "intent": intent,
            "plan": plan,
            "extracted": extracted,
        }

    if intent == "ans_ques":
        plan = [{"step": 1, "tool": "ans_ques", "status": "running"}]
        out = answer(ctx, query)
        plan[0]["status"] = "failed" if out.get("error") else "done"
        return {
            "need_clr": False,
            "question": None,
            "answer": out.get("text", "") if not out.get("error") else out["error"],
            "intent": intent,
            "plan": plan,
            "extracted": extracted,
        }

    if intent == "sentiment":
        plan = [{"step": 1, "tool": "sentiment", "status": "running"}]
        out = sentiment(ctx)
        plan[0]["status"] = "failed" if out.get("error") else "done"
        return {
            "need_clr": False,
            "question": None,
            "answer": out.get("text", "") if not out.get("error") else out["error"],
            "intent": intent,
            "plan": plan,
            "extracted": extracted,
        }

    if intent == "explain_code":
        plan = [{"step": 1, "tool": "explain_code", "status": "running"}]
        out = explain(ctx, query)
        plan[0]["status"] = "failed" if out.get("error") else "done"
        return {
            "need_clr": False,
            "question": None,
            "answer": out.get("text", "") if not out.get("error") else out["error"],
            "intent": intent,
            "plan": plan,
            "extracted": extracted,
        }

    if intent == "compare":
        if len(extracted) < 2:
            return {
                "need_clr": False,
                "question": None,
                "answer": "Need at least 2 inputs to compare",
                "intent": intent,
                "plan": [],
                "extracted": extracted,
            }
        plan = [{"step": 1, "tool": "compare", "status": "running"}]
        out = compare(ctx, query)
        plan[0]["status"] = "failed" if out.get("error") else "done"
        return {
            "need_clr": False,
            "question": None,
            "answer": out.get("text", "") if not out.get("error") else out["error"],
            "intent": intent,
            "plan": plan,
            "extracted": extracted,
        }

    if intent == "fetch_youtube":
        urls = find_urls(f"{query}\n{ctx}")
        if not urls:
            return {
                "need_clr": False,
                "question": None,
                "answer": "No YouTube URL found in the inputs",
                "intent": intent,
                "plan": [{"step": 1, "tool": "find_url", "status": "failed"}],
                "extracted": extracted,
            }

        plan = [
            {"step": 1, "tool": "find_url", "status": "done"},
            {"step": 2, "tool": "fetch_youtube", "status": "running"},
        ]
        yt = ext_yt(urls[0])
        if yt.get("error"):
            plan[1]["status"] = "failed"
            return {
                "need_clr": False,
                "question": None,
                "answer": yt["error"],
                "intent": intent,
                "plan": plan,
                "extracted": extracted,
            }
        plan[1]["status"] = "done"
        plan.append({"step": 3, "tool": "summarize", "status": "running"})
        out = summarize(yt["text"], query)
        plan[2]["status"] = "failed" if out.get("error") else "done"
        return {
            "need_clr": False,
            "question": None,
            "answer": out.get("text", "") if not out.get("error") else out["error"],
            "intent": intent,
            "plan": plan,
            "extracted": extracted,
        }

    return {
        "need_clr": False,
        "question": None,
        "answer": "",
        "intent": intent,
        "plan": [],
        "extracted": extracted,
    }


def build_ctx(extracted: list[dict]) -> str:
    parts = []
    for item in extracted:
        label = item.get("name") or item.get("type") or "input"
        text = item.get("text", "").strip()
        if text:
            parts.append(f"[{label}]\n{text}")
    return "\n\n".join(parts)


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
