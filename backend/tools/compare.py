from llm import text

PROMPT = """Compare the inputs below and answer the question.
Cover: same topic or not, key similarities, key differences.

Question: {query}

{context}"""


def compare(context: str, query: str) -> dict:
    if not context.strip():
        return {"text": "", "error": "No content to compare"}
    q = query.strip() or "Do these inputs discuss the same topic?"
    return text(PROMPT.format(query=q, context=context))
