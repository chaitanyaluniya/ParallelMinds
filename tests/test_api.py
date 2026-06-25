import pytest


@pytest.mark.asyncio
async def test_health(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_process_routes_to_agent(client, monkeypatch):
    def fake_run(query, types, extracted=None):
        return {
            "need_clr": False,
            "question": None,
            "answer": "mock answer",
            "intent": "ans_ques",
            "plan": [{"step": 1, "tool": "ans_ques", "status": "done"}],
            "extracted": extracted or [],
        }

    monkeypatch.setattr("main.run", fake_run)
    res = await client.post("/api/process", data={"query": "hello"})
    assert res.status_code == 200
    assert res.json()["answer"] == "mock answer"
