from app.models.schemas import ExtractedContent, ToolResult
from app.tools.base import BaseTool


class AudioTranscribeTool(BaseTool):
    name = "audio_transcribe"
    description = "Transcribe audio (MP3/WAV/M4A) to cleaned text"

    async def run(
        self, query: str, extracted: list[ExtractedContent], context: dict
    ) -> ToolResult:
        # TODO: openai-whisper implementation
        return ToolResult(
            tool_name=self.name,
            success=True,
            output="Audio transcription not yet implemented.",
            metadata={"duration_seconds": None},
        )
