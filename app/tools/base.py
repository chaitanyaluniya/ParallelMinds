from abc import ABC, abstractmethod

from app.models.schemas import ExtractedContent, ToolResult


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    async def run(
        self,
        query: str,
        extracted: list[ExtractedContent],
        context: dict,
    ) -> ToolResult:
        ...
