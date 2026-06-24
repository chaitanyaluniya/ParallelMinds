"""Tool registry — maps tool names to implementations."""

from app.models.schemas import ExtractedContent, ToolResult
from app.tools.audio_transcribe import AudioTranscribeTool
from app.tools.base import BaseTool
from app.tools.code_explainer import CodeExplainerTool
from app.tools.conversational import ConversationalTool
from app.tools.cross_input import CrossInputCompareTool
from app.tools.ocr import OCRTool
from app.tools.pdf_parser import PDFParserTool
from app.tools.sentiment import SentimentTool
from app.tools.summarizer import SummarizerTool
from app.tools.youtube import YouTubeTranscriptTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        for tool in [
            OCRTool(),
            PDFParserTool(),
            AudioTranscribeTool(),
            YouTubeTranscriptTool(),
            SummarizerTool(),
            SentimentTool(),
            CodeExplainerTool(),
            ConversationalTool(),
            CrossInputCompareTool(),
        ]:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, str]]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]

    async def execute(
        self,
        tool_name: str,
        query: str,
        extracted: list[ExtractedContent],
        context: dict,
    ) -> ToolResult:
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output=f"Unknown tool: {tool_name}",
            )
        return await tool.run(query=query, extracted=extracted, context=context)
