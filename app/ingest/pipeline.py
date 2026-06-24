"""Multi-input ingestion pipeline — extract content from text + files."""

import uuid

from fastapi import UploadFile

from app.ingest.validators import validate_file
from app.models.schemas import ExtractedContent, InputType


class IngestPipeline:
    """
    Accepts text query and multiple files; returns unified extracted content list.
    TODO: Implement per-type extractors (OCR, PDF, audio).
    """

    async def process(self, query: str, files: list[UploadFile]) -> list[ExtractedContent]:
        results: list[ExtractedContent] = []

        if query.strip():
            results.append(
                ExtractedContent(
                    source_id=str(uuid.uuid4()),
                    input_type=InputType.TEXT,
                    filename=None,
                    text=query.strip(),
                )
            )

        for file in files:
            validate_file(file)
            content_type = file.content_type or ""
            input_type = self._detect_type(content_type)
            raw_bytes = await file.read()

            # Placeholder extraction — wire to tools in next phase
            text = await self._extract_placeholder(input_type, raw_bytes, file.filename)
            results.append(
                ExtractedContent(
                    source_id=str(uuid.uuid4()),
                    input_type=input_type,
                    filename=file.filename,
                    text=text,
                    metadata={"content_type": content_type, "size_bytes": len(raw_bytes)},
                )
            )

        return results

    def _detect_type(self, content_type: str) -> InputType:
        if content_type.startswith("image/"):
            return InputType.IMAGE
        if content_type == "application/pdf":
            return InputType.PDF
        return InputType.AUDIO

    async def _extract_placeholder(
        self, input_type: InputType, raw_bytes: bytes, filename: str | None
    ) -> str:
        return f"[{input_type.value} extraction pending for {filename or 'upload'}]"
