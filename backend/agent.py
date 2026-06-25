import json
import os
import re

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

INTENTS = {
    "summarize",
    "answer_question",
    "sentiment",
    "explain_code",
    "compare",
    "fetch_youtube",
}

PROMPT = """Classify intent from the query and input types.
JSON only: {{"intent":"...","needs_clarification":false,"question":null}}

Intents:
- summarize — wants summary (1-line, bullets, paragraph)
- answer_question — general Q&A about the content
- sentiment — sentiment label + justification
- explain_code — explain code, find bugs, mention complexity
- compare — compare content across multiple inputs
- fetch_youtube — fetch/summarize a YouTube URL found in the content

needs_clarification=true if task is unclear, vague (e.g. "do something with this"), or multiple intents fit equally.
If true, question must be one short follow-up.

Query: {query}
Input types: {types}
"""


def cls_intent(query: str, types: list[str]) -> dict:
    if not query.strip() and not types:
        return {
            "intent": None,
            "needs_clarification": True,
            "question": "What would you like me to do?",
        }

    if not query.strip() and types:
        return {
            "intent": None,
            "needs_clarification": True,
            "question": "What do you want me to do with these files?",
        }

    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return {"intent": None, "needs_clarification": True, "question": None, "error": "GOOGLE_API_KEY not set"}

    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
        res = model.generate_content(
            PROMPT.format(query=query.strip(), types=", ".join(types) or "none")
        )
        if not res.text:
            return {"intent": None, "needs_clarification": True, "question": None, "error": "Empty Gemini response"}
        return prs_intent(res.text.strip())
    except (GoogleAPIError, ValueError) as e:
        return {"intent": None, "needs_clarification": True, "question": None, "error": f"Classification failed: {e}"}


def run(query: str, types: list[str]) -> dict:
    result = cls_intent(query, types)

    if result.get("error"):
        return {
            "needs_clarification": True,
            "question": result["error"],
            "answer": "",
            "intent": None,
            "plan": [],
        }

    if result.get("needs_clarification"):
        return {
            "needs_clarification": True,
            "question": result.get("question") or "Could you clarify what you'd like me to do?",
            "answer": "",
            "intent": result.get("intent"),
            "plan": [],
        }

    return {
        "needs_clarification": False,
        "question": None,
        "answer": "",
        "intent": result["intent"],
        "plan": [],
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
            intent = "answer_question"
        return {
            "intent": intent,
            "needs_clarification": bool(data.get("needs_clarification")),
            "question": data.get("question"),
        }
    except json.JSONDecodeError:
        return {"intent": "answer_question", "needs_clarification": False, "question": None}
