import os

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

SUM_PROMPT = """Summarize the content below.
Format exactly:
ONE-LINE: ...
BULLETS:
- ...
- ...
- ...
PARAGRAPH: (exactly 5 sentences)

{hint}
Content:
{context}"""

QA_PROMPT = """Answer the question using the content below. Be friendly and concise.

Question: {query}

Content:
{context}"""


def summarize(context: str, query: str = "") -> dict:
    hint = f"Focus: {query}" if query.strip() else ""
    return call(SUM_PROMPT.format(hint=hint, context=context or "(no content)"))


def answer(context: str, query: str) -> dict:
    if not query.strip():
        return {"text": "", "error": "No question provided"}
    return call(QA_PROMPT.format(query=query.strip(), context=context or "(no content)"))


def call(prompt: str) -> dict:
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return {"text": "", "error": "GOOGLE_API_KEY not set"}
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
        res = model.generate_content(prompt)
        if not res.text:
            return {"text": "", "error": "Empty Gemini response"}
        return {"text": res.text.strip()}
    except (GoogleAPIError, ValueError) as e:
        return {"text": "", "error": f"Generation failed: {e}"}
