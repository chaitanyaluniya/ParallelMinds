import pytest

from app.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_registry_lists_all_tools():
    registry = ToolRegistry()
    tools = registry.list_tools()
    names = {t["name"] for t in tools}
    assert "summarize" in names
    assert "youtube_transcript" in names
    assert "code_explain" in names


@pytest.mark.asyncio
async def test_unknown_tool_returns_error():
    registry = ToolRegistry()
    result = await registry.execute("nonexistent_tool", "", [], {})
    assert result.success is False
