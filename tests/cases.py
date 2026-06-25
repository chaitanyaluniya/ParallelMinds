import pytest

from agent import run


def intent(name):
    return {"intent": name, "need_clr": False, "question": None}


@pytest.fixture
def patch_intent(monkeypatch):
    def _set(name):
        monkeypatch.setattr("agent.cls_intent", lambda q, t: intent(name))
    return _set


def tc1(patch_intent, monkeypatch):
    patch_intent("summarize")
    summary = "ONE-LINE: ML lecture intro\nBULLETS:\n- gradients\n- loss\n- optimizers\nPARAGRAPH: Five sentences here."
    monkeypatch.setattr("agent.summarize", lambda ctx, q: {"text": summary})

    extracted = [{
        "type": "audio",
        "name": "lecture.mp3",
        "text": "Today we cover gradient descent and loss functions for neural networks.",
        "duration": 300,
    }]
    result = run("summarize this lecture", ["audio", "text"], extracted)

    assert result["intent"] == "summarize"
    assert "ONE-LINE" in result["answer"]
    assert "BULLETS" in result["answer"]
    assert result["plan"][0]["tool"] == "summarize"
    assert result["plan"][0]["status"] == "done"


def tc2(patch_intent, monkeypatch):
    patch_intent("ans_ques")
    monkeypatch.setattr(
        "agent.answer",
        lambda ctx, q: {"text": "- Ship v1 by Friday\n- Review API docs\n- Schedule QA sync"},
    )

    extracted = [{
        "type": "pdf",
        "name": "notes.pdf",
        "text": "Meeting notes\nAction item: ship v1 by Friday\nAction item: review API docs\nAction item: schedule QA sync",
    }]
    result = run("What are the action items?", ["pdf", "text"], extracted)

    assert result["intent"] == "ans_ques"
    assert "Ship v1" in result["answer"]
    assert "API docs" in result["answer"]


def tc3(patch_intent, monkeypatch):
    patch_intent("explain_code")
    code_out = "Language: Python\nBug: missing base case causes RecursionError\nComplexity: O(2^n)"
    monkeypatch.setattr("agent.explain", lambda ctx, q: {"text": code_out})

    extracted = [{
        "type": "image",
        "name": "code.png",
        "text": "def fib(n):\n  if n <= 1: return n\n  return fib(n-1)+fib(n-2)",
    }]
    result = run("Explain", ["image", "text"], extracted)

    assert result["intent"] == "explain_code"
    assert "Bug" in result["answer"] or "RecursionError" in result["answer"]
    assert "Complexity" in result["answer"]


def tc4(patch_intent, monkeypatch):
    patch_intent("fetch_youtube")
    monkeypatch.setattr(
        "agent.ext_yt",
        lambda url: {"text": "Never gonna give you up transcript content here.", "video_id": "dQw4w9WgXcQ"},
    )
    monkeypatch.setattr(
        "agent.summarize",
        lambda ctx, q: {"text": "ONE-LINE: Rick Astley song summary\nBULLETS:\n- commitment\n- loyalty\n- classic hit\nPARAGRAPH: Five sentence summary."},
    )

    extracted = [{
        "type": "pdf",
        "name": "doc.pdf",
        "text": "Reference video: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }]
    result = run("Hit the YT URL and summarize it", ["pdf", "text"], extracted)

    assert result["intent"] == "fetch_youtube"
    assert len(result["plan"]) == 3
    assert result["plan"][0]["tool"] == "find_url"
    assert result["plan"][1]["tool"] == "fetch_youtube"
    assert result["plan"][2]["tool"] == "summarize"
    assert "ONE-LINE" in result["answer"]


def tc5(patch_intent, monkeypatch):
    patch_intent("compare")
    monkeypatch.setattr(
        "agent.compare",
        lambda ctx, q: {"text": "Yes, both discuss gradient descent and neural network optimization."},
    )

    extracted = [
        {"type": "audio", "name": "lecture.mp3", "text": "Today we discuss gradient descent for training neural nets."},
        {"type": "pdf", "name": "notes.pdf", "text": "Chapter 3 covers optimization and gradient descent methods."},
    ]
    result = run("Do the audio and document discuss the same topic?", ["audio", "pdf", "text"], extracted)

    assert result["intent"] == "compare"
    assert "gradient descent" in result["answer"].lower()
    assert result["plan"][0]["tool"] == "compare"

