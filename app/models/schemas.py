from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class InputType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    AUDIO = "audio"


class ExtractedContent(BaseModel):
    """Content extracted from a single input source."""

    source_id: str
    input_type: InputType
    filename: str | None = None
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None


class PlanStep(BaseModel):
    """One step in the agent's execution plan."""

    step_number: int
    tool_name: str
    description: str
    status: str = "pending"  # pending | running | completed | failed
    result_summary: str | None = None


class ToolResult(BaseModel):
    """Output from a single tool invocation."""

    tool_name: str
    success: bool
    output: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Final response returned to the client."""

    needs_clarification: bool = False
    clarification_question: str | None = None
    extracted_contents: list[ExtractedContent] = Field(default_factory=list)
    plan_trace: list[PlanStep] = Field(default_factory=list)
    final_answer: str = ""
    tool_results: list[ToolResult] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """JSON body for text-only chat (no file uploads)."""

    query: str
    session_id: str | None = None
