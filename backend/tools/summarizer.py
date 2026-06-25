from format import fmt_summary
from llm import ask

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


def summarize(context: str, query: str = "", on_chunk=None) -> dict:
    out = ask(sum_prompt(context, query), on_chunk)
    if out.get("text"):
        out["text"] = fmt_summary(out["text"])
    return out


def answer(context: str, query: str, on_chunk=None) -> dict:
    if not query.strip():
        return {"text": "", "error": "No question provided"}
    return ask(qa_prompt(context, query), on_chunk)


def sum_prompt(context: str, query: str = "") -> str:
    hint = f"Focus: {query}" if query.strip() else ""
    return SUM_PROMPT.format(hint=hint, context=context or "(no content)")


def qa_prompt(context: str, query: str) -> str:
    return QA_PROMPT.format(query=query.strip(), context=context or "(no content)")
