import os

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

PROMPT = """Compare the inputs below and answer the question.
Cover: same topic or not, key similarities, key differences.

Question: {query}

{context}"""


def compare(context: str, query: str) -> dict:
    if not context.strip():
        return {"text": "", "error": "No content to compare"}
    q = query.strip() or "Do these inputs discuss the same topic?"
    return call(PROMPT.format(query=q, context=context))


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
        return {"text": "", "error": f"Compare failed: {e}"}
