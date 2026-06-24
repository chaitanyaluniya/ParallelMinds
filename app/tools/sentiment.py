from app.models.schemas import ExtractedContent, ToolResult
from app.tools.base import BaseTool


class SentimentTool(BaseTool):
    name = "sentiment_analysis"
    description = "Label sentiment with confidence and one-line justification"

    async def run(
        self, query: str, extracted: list[ExtractedContent], context: dict
    ) -> ToolResult:
        # TODO: LLM or classifier-based sentiment
        return ToolResult(
            tool_name=self.name,
            success=True,
            output="Sentiment analysis not yet implemented.",
        )
