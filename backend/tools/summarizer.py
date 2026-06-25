from format import fmt_summary, strip_md
from llm import text

SUM_PROMPT = """Summarize the content below.
Plain text only — no markdown, no asterisks.

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
    out = text(SUM_PROMPT.format(hint=hint, context=context or "(no content)"))
    if out.get("text"):
        out["text"] = fmt_summary(out["text"])
    return out


def answer(context: str, query: str) -> dict:
    if not query.strip():
        return {"text": "", "error": "No question provided"}
    return text(QA_PROMPT.format(query=query.strip(), context=context or "(no content)"))
