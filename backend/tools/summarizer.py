from llm import text

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
    return text(SUM_PROMPT.format(hint=hint, context=context or "(no content)"))


def answer(context: str, query: str) -> dict:
    if not query.strip():
        return {"text": "", "error": "No question provided"}
    return text(QA_PROMPT.format(query=query.strip(), context=context or "(no content)"))
