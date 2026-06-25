from llm import text

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
    return text(PROMPT.format(context=context))
