from llm import ask

PROMPT = """Analyze sentiment of the content below.
Format exactly:
LABEL: positive|negative|neutral|mixed
CONFIDENCE: high|medium|low
JUSTIFICATION: (one line)

Content:
{context}"""


def sentiment(context: str, on_chunk=None) -> dict:
    if not context.strip():
        return {"text": "", "error": "No content to analyze"}
    return ask(sent_prompt(context), on_chunk)


def sent_prompt(context: str) -> str:
    return PROMPT.format(context=context)
