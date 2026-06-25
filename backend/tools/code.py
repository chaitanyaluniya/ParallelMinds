import re

from format import strip_md
from llm import text

PROMPT = """Explain the code below.
Plain text only — no markdown, no asterisks, no backticks.

Include:
- what it does (step by step)
- detected language
- any bugs or issues
- time complexity

{hint}
Code:
{code}"""

CODE_HINT = re.compile(
    r"(#include|def |class |int main|void |function |public static|=>|std::|vector<|console\.log)",
    re.I,
)


def explain(context: str, query: str = "") -> dict:
    code = context.strip() or code_from_query(query)
    if not code.strip():
        return {"text": "", "error": "No code found in the input"}
    hint = f"User note: {query}" if query.strip() else ""
    out = text(PROMPT.format(hint=hint, code=code))
    if out.get("text"):
        out["text"] = strip_md(out["text"])
    return out


def code_from_query(query: str) -> str:
    q = query.strip()
    for phrase in [
        r"explain the code",
        r"explain this code",
        r"explain this",
        r"what does this code do",
        r"explain",
    ]:
        q = re.sub(phrase, "", q, flags=re.I).strip()
    return q if looks_like_code(q) else query.strip()


def looks_like_code(s: str) -> bool:
    return bool(CODE_HINT.search(s)) or s.count("{") >= 2 or s.count(";") >= 3
