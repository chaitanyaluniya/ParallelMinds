from app.models.schemas import ExtractedContent, ToolResult
from app.tools.base import BaseTool


class ConversationalTool(BaseTool):
    name = "conversational_answer"
    description = "Friendly, helpful response for general questions"

    async def run(
        self, query: str, extracted: list[ExtractedContent], context: dict
    ) -> ToolResult:
        context_text = "\n\n".join(
            f"[{e.input_type.value}] {e.text}" for e in extracted if e.text
        )
        answer = f"Query received: {query or '(no query)'}"
        if context_text:
            answer += f"\n\nContext from inputs:\n{context_text[:500]}"
        answer += "\n\n(Full conversational LLM response pending implementation.)"
        return ToolResult(tool_name=self.name, success=True, output=answer)
