import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_chat_text_only(client):
    response = await client.post(
        "/api/chat",
        data={"query": "Hello, what can you do?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "final_answer" in data
    assert data["extracted_contents"]


@pytest.mark.asyncio
async def test_chat_empty_requires_clarification(client):
    response = await client.post("/api/chat", data={"query": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["needs_clarification"] is True
