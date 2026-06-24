"""Agent orchestrator — coordinates ingest, planning, and tool execution."""

from fastapi import UploadFile

from app.agent.planner import AgentPlanner
from app.ingest.pipeline import IngestPipeline
from app.models.schemas import AgentResponse, ExtractedContent, PlanStep, ToolResult
from app.tools.registry import ToolRegistry


class AgentOrchestrator:
    def __init__(self) -> None:
        self.ingest = IngestPipeline()
        self.planner = AgentPlanner()
        self.tools = ToolRegistry()

    async def run(self, query: str, files: list[UploadFile]) -> AgentResponse:
        extracted: list[ExtractedContent] = await self.ingest.process(query=query, files=files)

        plan = await self.planner.create_plan(query=query, extracted=extracted)

        if plan.needs_clarification:
            return AgentResponse(
                needs_clarification=True,
                clarification_question=plan.clarification_question,
                extracted_contents=extracted,
                plan_trace=[],
                final_answer=plan.clarification_question or "",
            )

        plan_trace: list[PlanStep] = []
        tool_results: list[ToolResult] = []

        for idx, step in enumerate(plan.steps, start=1):
            plan_step = PlanStep(
                step_number=idx,
                tool_name=step.tool_name,
                description=step.description,
                status="running",
            )
            plan_trace.append(plan_step)

            result = await self.tools.execute(
                tool_name=step.tool_name,
                query=query,
                extracted=extracted,
                context=step.context,
            )
            tool_results.append(result)
            plan_step.status = "completed" if result.success else "failed"
            plan_step.result_summary = result.output[:200] if result.output else None

        final_answer = await self.planner.synthesize(
            query=query,
            extracted=extracted,
            tool_results=tool_results,
        )

        return AgentResponse(
            extracted_contents=extracted,
            plan_trace=plan_trace,
            tool_results=tool_results,
            final_answer=final_answer,
        )
