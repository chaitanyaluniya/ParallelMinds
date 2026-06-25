import os

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

PROMPT = """Explain the code below.
Include:
- what it does (step by step)
- detected language
- any bugs or issues
- time complexity

{hint}
Code:
{context}"""


def explain(context: str, query: str = "") -> dict:
    if not context.strip():
        return {"text": "", "error": "No code found in the input"}
    hint = f"User note: {query}" if query.strip() else ""
    return call(PROMPT.format(hint=hint, context=context))


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
        return {"text": "", "error": f"Code explanation failed: {e}"}
