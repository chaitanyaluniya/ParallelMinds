from collections import defaultdict

MAX = int(__import__("os").getenv("MAX_HISTORY", "8"))

_store: dict[str, list[dict]] = defaultdict(list)
_pending: dict[str, list[dict]] = {}
_asked: set[str] = set()


def get(sid: str) -> list[dict]:
    if not sid:
        return []
    return list(_store[sid][-MAX:])


def add(sid: str, user: str, bot: str):
    if not sid:
        return
    u = user.strip() or "(upload)"
    _store[sid].append({"user": u, "bot": (bot or "").strip()})
    _store[sid] = _store[sid][-MAX:]


def set_pend(sid: str, extracted: list[dict]):
    if not sid or not extracted:
        return
    _pending[sid] = [dict(item) for item in extracted]


def get_pend(sid: str) -> list[dict]:
    if not sid:
        return []
    return [dict(item) for item in _pending.get(sid, [])]


def pop_pend(sid: str) -> list[dict]:
    if not sid:
        return []
    return _pending.pop(sid, [])


def clear_pend(sid: str):
    if sid:
        _pending.pop(sid, None)
        _asked.discard(sid)


def mark_asked(sid: str):
    if sid:
        _asked.add(sid)


def was_asked(sid: str) -> bool:
    return bool(sid) and sid in _asked


def ctx(sid: str) -> str:
    lines = []
    for turn in get(sid):
        lines.append(f"User: {turn['user']}\nAssistant: {turn['bot']}")
    if not lines:
        return ""
    return "Recent conversation:\n" + "\n\n".join(lines)
