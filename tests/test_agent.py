import pytest

from app.agent.planner import AgentPlanner
from app.models.schemas import ExtractedContent, InputType


@pytest.mark.asyncio
async def test_planner_asks_clarification_when_no_query_and_no_files():
    planner = AgentPlanner()
    plan = await planner.create_plan(query="", extracted=[])
    assert plan.needs_clarification is True


@pytest.mark.asyncio
async def test_planner_asks_clarification_when_files_but_no_query():
    planner = AgentPlanner()
    extracted = [
        ExtractedContent(
            source_id="1",
            input_type=InputType.PDF,
            filename="notes.pdf",
            text="Some meeting notes",
        )
    ]
    plan = await planner.create_plan(query="", extracted=extracted)
    assert plan.needs_clarification is True
    assert "extracted text" in (plan.clarification_question or "").lower()


@pytest.mark.asyncio
async def test_planner_creates_steps_for_valid_query():
    planner = AgentPlanner()
    plan = await planner.create_plan(
        query="Summarize this document",
        extracted=[
            ExtractedContent(
                source_id="1",
                input_type=InputType.TEXT,
                text="Summarize this document",
            )
        ],
    )
    assert plan.needs_clarification is False
    assert len(plan.steps) >= 1
