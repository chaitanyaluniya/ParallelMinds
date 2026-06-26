import pytest

from agent import run
from agent import rule_intent as detect_intent
from format import fmt_summary as format_summary, strip_md
from limits import trim, tokens
from mem import add, ctx
import rag
from tools.code import looks_like_code


def intent(name):
    return {"intent": name, "need_clr": False, "question": None}


@pytest.fixture
def patch_intent(monkeypatch):
    def _set(name):
        monkeypatch.setattr("agent.cls_intent", lambda q, t, e, sid="": intent(name))
    return _set


def patch_llm(monkeypatch, text):
    def fake(prompt, fmt=None):
        out = fmt(text) if fmt else text
        yield {"type": "token", "text": out}
        return (out, None)

    monkeypatch.setattr("agent.stream_llm", fake)


def tc1(patch_intent, monkeypatch):
    patch_intent("summarize")
    summary = "ONE-LINE: ML lecture intro\nBULLETS:\n- gradients\n- loss\n- optimizers\nPARAGRAPH: Five sentences here."
    patch_llm(monkeypatch, summary)

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
    patch_llm(monkeypatch, "- Ship v1 by Friday\n- Review API docs\n- Schedule QA sync")

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
    patch_llm(monkeypatch, "Language: Python\nBug: RecursionError\nComplexity: O(2^n)")

    extracted = [{"type": "image", "name": "code.png", "text": "def fib(n): return fib(n-1)"}]
    result = run("Explain", ["image", "text"], extracted)

    assert result["intent"] == "explain_code"
    assert "Complexity" in result["answer"]


def tc3b(monkeypatch):
    monkeypatch.setattr("agent.cls_intent", lambda q, t, e, sid="": intent("explain_code"))
    patch_llm(monkeypatch, "Language: C++\nComplexity: O(n)")

    code = "#include<bits/stdc++.h>\nclass Solution { public: int trap() { return 0; } };"
    result = run(f"{code}\nexplain the code", ["text"], [])

    assert result["intent"] == "explain_code"
    assert "Complexity" in result["answer"]


def tc4(patch_intent, monkeypatch):
    patch_intent("fetch_youtube")
    monkeypatch.setattr("agent.ext_yt", lambda url: {"text": "transcript text here", "video_id": "dQw4w9WgXcQ"})
    patch_llm(monkeypatch, "ONE-LINE: summary\nBULLETS:\n- a\n- b\n- c\nPARAGRAPH: five sentences.")

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
    patch_llm(monkeypatch, "Yes, both discuss gradient descent.")

    extracted = [
        {"type": "audio", "name": "lecture.mp3", "text": "gradient descent for neural nets"},
        {"type": "pdf", "name": "notes.pdf", "text": "optimization and gradient descent"},
    ]
    result = run("Do the audio and document discuss the same topic?", ["audio", "pdf", "text"], extracted)

    assert result["intent"] == "compare"
    assert "gradient descent" in result["answer"].lower()


def rule_yt():
    assert detect_intent("provide transcript https://youtu.be/dQw4w9WgXcQ", ["text"], []) == "fetch_youtube"


def rule_doc_q():
    pdf = [{"type": "pdf", "name": "doc.pdf", "text": "Action Items table here"}]
    assert detect_intent("fetch actions", ["pdf", "text"], pdf) == "ans_ques"
    assert detect_intent("get the deadlines", ["pdf", "text"], pdf) == "ans_ques"
    assert detect_intent("show owners", ["pdf", "text"], pdf) == "ans_ques"
    assert detect_intent("do something with this", ["pdf", "text"], pdf) is None

    # sparse PDF text still routes to Q&A, not clarification loop
    sparse = [{"type": "pdf", "name": "scan.pdf", "text": ""}]
    assert detect_intent("fetch actions", ["pdf", "text"], sparse) == "ans_ques"


def test_no_loop(monkeypatch):
    from agent import cls_intent
    from mem import clear_pend, get_pend, mark_asked, set_pend

    pdf = [{"type": "pdf", "name": "doc.pdf", "text": "Action item: ship v1 by Friday"}]
    sid = "loop_sid"
    clear_pend(sid)
    set_pend(sid, pdf)
    mark_asked(sid)

    result = cls_intent("fetch actions", ["pdf", "text"], pdf, sid)
    assert result["need_clr"] is False
    assert result["intent"] == "ans_ques"
    clear_pend(sid)


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


def test_trim():
    long = "word " * 5000
    out, cut = trim(long, 100)
    assert cut is True
    assert "truncated" in out


def test_mem():
    add("tc_sid", "hello", "hi")
    assert "hello" in ctx("tc_sid")


def test_pending(patch_intent, monkeypatch):
    from mem import clear_pend, get_pend, set_pend

    patch_intent("summarize")
    pdf_txt = "Quarterly report on machine learning adoption in healthcare systems."
    patch_llm(monkeypatch, f"ONE-LINE: ML in healthcare\nBULLETS:\n- adoption\nPARAGRAPH: {pdf_txt}")

    set_pend("pend_sid", [{"type": "pdf", "name": "report.pdf", "text": pdf_txt}])
    assert get_pend("pend_sid")

    pending = get_pend("pend_sid")
    result = run("summarize", ["pdf", "text"], pending, sid="pend_sid")
    assert result["intent"] == "summarize"
    assert result["extracted"][0]["name"] == "report.pdf"
    assert not get_pend("pend_sid")

    clear_pend("pend_sid")


def test_rag(monkeypatch):
    monkeypatch.setattr("rag.embed", lambda texts: [[1.0, 0.0, 0.0] for _ in texts])
    long_txt = "Action item: ship v1 by Friday. " * 120
    rag.index("rag_sid", [{"name": "notes.pdf", "text": long_txt}])
    hits = rag.search("rag_sid", "what are the action items?", k=3)
    assert "Action item" in hits
    assert rag.should([{"text": long_txt}])
