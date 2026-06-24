"""Intent understanding and tool-sequence planning."""

from dataclasses import dataclass, field

from app.models.schemas import ExtractedContent, ToolResult


@dataclass
class PlannedStep:
    tool_name: str
    description: str
    context: dict = field(default_factory=dict)


@dataclass
class Plan:
    steps: list[PlannedStep] = field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: str | None = None


class AgentPlanner:
    """
    Determines user intent and builds a minimal tool sequence.
    TODO: Wire to OpenAI for intent classification and planning.
    """

    async def create_plan(self, query: str, extracted: list[ExtractedContent]) -> Plan:
        if not query.strip() and not extracted:
            return Plan(
                needs_clarification=True,
                clarification_question="What would you like me to do with your inputs?",
            )

        if not query.strip() and extracted:
            return Plan(
                needs_clarification=True,
                clarification_question="What do you want me to do with this extracted text?",
            )

        # Placeholder: single conversational step until LLM planner is implemented
        return Plan(
            steps=[
                PlannedStep(
                    tool_name="conversational_answer",
                    description="Answer the user's query using extracted context",
                    context={"query": query},
                )
            ]
        )

    async def synthesize(
        self,
        query: str,
        extracted: list[ExtractedContent],
        tool_results: list[ToolResult],
    ) -> str:
        if tool_results:
            return tool_results[-1].output
        return "No result produced."
