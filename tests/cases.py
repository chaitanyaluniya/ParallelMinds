import pytest

from agent import run
from agent import rule_intent as detect_intent
from format import fmt_summary as format_summary, strip_md
from tools.code import looks_like_code


def intent(name):
    return {"intent": name, "need_clr": False, "question": None}


@pytest.fixture
def patch_intent(monkeypatch):
    def _set(name):
        monkeypatch.setattr("agent.cls_intent", lambda q, t, e: intent(name))
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


def tc2(patch_intent, monkeypatch):
    patch_intent("ans_ques")
    monkeypatch.setattr(
        "agent.answer",
        lambda ctx, q: {"text": "- Ship v1 by Friday\n- Review API docs\n- Schedule QA sync"},
    )

    extracted = [{
        "type": "pdf",
        "name": "notes.pdf",
        "text": "Meeting notes\nAction item: ship v1 by Friday\nAction item: review API docs",
    }]
    result = run("What are the action items?", ["pdf", "text"], extracted)

    assert result["intent"] == "ans_ques"
    assert "Ship v1" in result["answer"]


def tc3(patch_intent, monkeypatch):
    patch_intent("explain_code")
    monkeypatch.setattr("agent.explain", lambda ctx, q: {"text": "Language: Python\nBug: RecursionError\nComplexity: O(2^n)"})

    extracted = [{"type": "image", "name": "code.png", "text": "def fib(n): return fib(n-1)"}]
    result = run("Explain", ["image", "text"], extracted)

    assert result["intent"] == "explain_code"
    assert "Complexity" in result["answer"]


def tc3b(monkeypatch):
    monkeypatch.setattr("agent.cls_intent", lambda q, t, e: intent("explain_code"))
    monkeypatch.setattr("agent.explain", lambda ctx, q: {"text": "Language: C++\nComplexity: O(n)"})

    code = "#include<bits/stdc++.h>\nclass Solution { public: int trap() { return 0; } };"
    result = run(f"{code}\nexplain the code", ["text"], [])

    assert result["intent"] == "explain_code"
    assert "Complexity" in result["answer"]


def tc4(patch_intent, monkeypatch):
    patch_intent("fetch_youtube")
    monkeypatch.setattr("agent.ext_yt", lambda url: {"text": "transcript text here", "video_id": "dQw4w9WgXcQ"})
    monkeypatch.setattr("agent.summarize", lambda ctx, q: {"text": "ONE-LINE: summary\nBULLETS:\n- a\n- b\n- c\nPARAGRAPH: five sentences."})

    extracted = [{"type": "pdf", "name": "doc.pdf", "text": "Video: https://www.youtube.com/watch?v=dQw4w9WgXcQ"}]
    result = run("summarize the youtube link", ["pdf", "text"], extracted)

    assert len(result["plan"]) == 3
    assert "ONE-LINE" in result["answer"]


def tc4b(monkeypatch):
    monkeypatch.setattr("agent.ext_yt", lambda url: {"text": "full transcript here", "video_id": "abc12345678"})
    result = run("https://www.youtube.com/watch?v=abc12345678 provide transcript", ["text"], [])

    assert result["intent"] == "fetch_youtube"
    assert result["answer"] == "full transcript here"
    assert len(result["plan"]) == 2


def tc5(patch_intent, monkeypatch):
    patch_intent("compare")
    monkeypatch.setattr("agent.compare", lambda ctx, q: {"text": "Yes, both discuss gradient descent."})

    extracted = [
        {"type": "audio", "name": "lecture.mp3", "text": "gradient descent for neural nets"},
        {"type": "pdf", "name": "notes.pdf", "text": "optimization and gradient descent"},
    ]
    result = run("Do the audio and document discuss the same topic?", ["audio", "pdf", "text"], extracted)

    assert result["intent"] == "compare"
    assert "gradient descent" in result["answer"].lower()


def rule_yt():
    assert detect_intent("provide transcript https://youtu.be/dQw4w9WgXcQ", ["text"], []) == "fetch_youtube"


def rule_code():
    code = "def foo():\n    return 1"
    assert detect_intent(f"{code}\nexplain", ["text"], []) == "explain_code"
    assert looks_like_code(code)


def fmt():
    raw = "**ONE-LINE:** hello\nBULLETS:\n- a\nPARAGRAPH: five sentences here."
    out = format_summary(raw)
    assert out.startswith("ONE-LINE:")
    assert "\n\nBULLETS:" in out
    assert "\n\nPARAGRAPH:" in out
    assert "**" not in out
    assert strip_md("**Overview**") == "Overview"
