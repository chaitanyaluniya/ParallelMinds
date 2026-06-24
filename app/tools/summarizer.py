from app.models.schemas import ExtractedContent, ToolResult
from app.tools.base import BaseTool


class SummarizerTool(BaseTool):
    name = "summarize"
    description = "Produce 1-line summary, 3 bullets, and 5-sentence summary"

    async def run(
        self, query: str, extracted: list[ExtractedContent], context: dict
    ) -> ToolResult:
        # TODO: LLM-powered summarization
        return ToolResult(
            tool_name=self.name,
            success=True,
            output="Summarization not yet implemented.",
        )
