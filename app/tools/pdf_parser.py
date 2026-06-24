from app.models.schemas import ExtractedContent, ToolResult
from app.tools.base import BaseTool


class PDFParserTool(BaseTool):
    name = "pdf_extract"
    description = "Parse PDF text with OCR fallback for scanned pages"

    async def run(
        self, query: str, extracted: list[ExtractedContent], context: dict
    ) -> ToolResult:
        # TODO: pymupdf + pdf2image OCR fallback
        return ToolResult(
            tool_name=self.name,
            success=True,
            output="PDF parsing not yet implemented.",
        )
