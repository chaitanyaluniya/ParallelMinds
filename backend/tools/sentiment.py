import os

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

PROMPT = """Analyze sentiment of the content below.
Format exactly:
LABEL: positive|negative|neutral|mixed
CONFIDENCE: high|medium|low
JUSTIFICATION: (one line)

Content:
{context}"""


def sentiment(context: str) -> dict:
    if not context.strip():
        return {"text": "", "error": "No content to analyze"}
    return call(PROMPT.format(context=context))


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
        return {"text": "", "error": f"Sentiment analysis failed: {e}"}
