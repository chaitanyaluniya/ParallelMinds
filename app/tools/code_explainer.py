from app.models.schemas import ExtractedContent, ToolResult
from app.tools.base import BaseTool


class CodeExplainerTool(BaseTool):
    name = "code_explain"
    description = "Explain code, detect bugs, and mention time complexity"

    async def run(
        self, query: str, extracted: list[ExtractedContent], context: dict
    ) -> ToolResult:
        # TODO: LLM code analysis
        return ToolResult(
            tool_name=self.name,
            success=True,
            output="Code explanation not yet implemented.",
        )
