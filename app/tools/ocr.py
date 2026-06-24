from app.models.schemas import ExtractedContent, ToolResult
from app.tools.base import BaseTool


class OCRTool(BaseTool):
    name = "ocr_extract"
    description = "Extract text from images using OCR with confidence scores"

    async def run(
        self, query: str, extracted: list[ExtractedContent], context: dict
    ) -> ToolResult:
        # TODO: pytesseract / Pillow implementation
        return ToolResult(
            tool_name=self.name,
            success=True,
            output="OCR extraction not yet implemented.",
            metadata={"confidence": None},
        )
