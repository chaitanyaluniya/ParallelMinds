from llm import text

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
    return text(PROMPT.format(hint=hint, context=context))
