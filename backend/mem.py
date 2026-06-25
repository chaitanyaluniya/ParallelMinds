from collections import defaultdict

MAX = int(__import__("os").getenv("MAX_HISTORY", "8"))

_store: dict[str, list[dict]] = defaultdict(list)


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


def ctx(sid: str) -> str:
    lines = []
    for turn in get(sid):
        lines.append(f"User: {turn['user']}\nAssistant: {turn['bot']}")
    if not lines:
        return ""
    return "Recent conversation:\n" + "\n\n".join(lines)
