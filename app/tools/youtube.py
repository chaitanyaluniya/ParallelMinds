import re

from app.models.schemas import ExtractedContent, ToolResult
from app.tools.base import BaseTool

YOUTUBE_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{11})"
)


class YouTubeTranscriptTool(BaseTool):
    name = "youtube_transcript"
    description = "Detect YouTube URLs and fetch video transcripts"

    async def run(
        self, query: str, extracted: list[ExtractedContent], context: dict
    ) -> ToolResult:
        combined = " ".join(e.text for e in extracted) + " " + query
        match = YOUTUBE_URL_PATTERN.search(combined)
        if not match:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="No YouTube URL found in the provided inputs.",
            )
        # TODO: youtube-transcript-api fetch
        video_id = match.group(1)
        return ToolResult(
            tool_name=self.name,
            success=True,
            output=f"YouTube transcript fetch pending for video: {video_id}",
            metadata={"video_id": video_id},
        )
