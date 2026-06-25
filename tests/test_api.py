import pytest

from limits import MAX_FILE


@pytest.mark.asyncio
async def test_health(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_estimate(client):
    res = await client.post(
        "/api/estimate",
        data={
            "query": "summarize this",
            "files_meta": '[{"name":"a.pdf","size":50000,"type":"application/pdf"}]',
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["cost_usd"] >= 0
    assert "summarize" in data["tools"]


@pytest.mark.asyncio
async def test_file_too_large(client):
    big = b"x" * (MAX_FILE + 1)
    res = await client.post(
        "/api/process",
        data={"query": "hi"},
        files={"files": ("big.pdf", big, "application/pdf")},
    )
    assert res.status_code == 413


@pytest.mark.asyncio
async def test_process_routes_to_agent(client, monkeypatch):
    def fake_run(query, types, extracted=None, sid=""):
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
