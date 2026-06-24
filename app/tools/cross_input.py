from app.models.schemas import ExtractedContent, ToolResult
from app.tools.base import BaseTool


class CrossInputCompareTool(BaseTool):
    name = "cross_input_compare"
    description = "Compare and reason across multiple input sources"

    async def run(
        self, query: str, extracted: list[ExtractedContent], context: dict
    ) -> ToolResult:
        # TODO: LLM comparative analysis
        sources = [f"{e.input_type.value}: {e.filename or 'text'}" for e in extracted]
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"Cross-input comparison pending. Sources: {', '.join(sources)}",
        )
