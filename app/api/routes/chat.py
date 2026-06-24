from fastapi import APIRouter, File, Form, UploadFile

from app.agent.core import AgentOrchestrator
from app.models.schemas import AgentResponse

router = APIRouter()
_orchestrator = AgentOrchestrator()


@router.post("/chat", response_model=AgentResponse)
async def chat(
    query: str = Form(default=""),
    files: list[UploadFile] = File(default=[]),
) -> AgentResponse:
    """
    Accept text query + optional multi-file uploads (image, PDF, audio).
    Returns extracted content, plan trace, and final text answer.
    """
    return await _orchestrator.run(query=query, files=files)
