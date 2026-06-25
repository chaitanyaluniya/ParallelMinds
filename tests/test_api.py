import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_process_empty(client):
    response = await client.post("/api/process", data={"query": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["need_clr"] is True


@pytest.mark.asyncio
async def test_process_text_only(client):
    response = await client.post("/api/process", data={"query": "hello"})
    assert response.status_code == 200
    assert "answer" in response.json()
