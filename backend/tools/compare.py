from llm import ask

PROMPT = """Compare the inputs below and answer the question.
Cover: same topic or not, key similarities, key differences.

Question: {query}

{context}"""


def compare(context: str, query: str, on_chunk=None) -> dict:
    if not context.strip():
        return {"text": "", "error": "No content to compare"}
    return ask(cmp_prompt(context, query), on_chunk)


def cmp_prompt(context: str, query: str) -> str:
    q = query.strip() or "Do these inputs discuss the same topic?"
    return PROMPT.format(query=q, context=context)
