import re

CHUNK = 900
OVERLAP = 120
TOP = 3
MIN_CHARS = 2500

_buckets = {}
_emb = None


def should(extracted):
    total = sum(len(i.get("text", "") or "") for i in extracted)
    return total >= MIN_CHARS


def chunk(txt):
    if len(txt) <= CHUNK:
        return [txt]
    parts = []
    start = 0
    while start < len(txt):
        parts.append(txt[start : start + CHUNK])
        start += CHUNK - OVERLAP
    return parts


def get_emb():
    global _emb
    if _emb is None:
        from fastembed import TextEmbedding
        _emb = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _emb


def embed(texts):
    return list(get_emb().embed(texts))


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb + 1e-9)


def index(sid, extracted):
    if not sid:
        return
    rows = []
    for item in extracted:
        txt = (item.get("text") or "").strip()
        if not txt:
            continue
        src = item.get("name") or item.get("type") or "doc"
        for piece in chunk(txt):
            rows.append({"src": src, "text": piece})
    if not rows:
        _buckets[sid] = []
        return
    vecs = embed([r["text"] for r in rows])
    for r, v in zip(rows, vecs):
        r["vec"] = list(v)
    _buckets[sid] = rows


def spread(sid, k=TOP):
    rows = _buckets.get(sid) or []
    if not rows:
        return ""
    if len(rows) <= k:
        picked = rows
    else:
        step = len(rows) / k
        picked = [rows[int(i * step)] for i in range(k)]
    return fmt_hits(picked)


def search(sid, query, k=TOP):
    rows = _buckets.get(sid) or []
    if not rows or not query.strip():
        return ""
    q = query.strip().lower()
    q_words = [w for w in re.findall(r"\w+", q) if len(w) > 2]
    qv = list(embed([query.strip()]))[0]

    scored = []
    for r in rows:
        sim = cosine(qv, r["vec"])
        txt = r["text"].lower()
        kw = sum(1 for w in q_words if w in txt) / max(len(q_words), 1)
        scored.append((sim + 0.25 * kw, r))

    scored.sort(key=lambda x: -x[0])
    picked = [r for _, r in scored[:k]]

    # pull chunks that literally mention query terms like "action" or "agenda"
    extra = []
    for r in rows:
        txt = r["text"].lower()
        if any(w in txt for w in q_words):
            if r not in picked and r not in extra:
                extra.append(r)
        if len(extra) >= 2:
            break

    return fmt_hits(picked + extra)


def fmt_hits(rows):
    parts = []
    seen = set()
    for r in rows:
        key = (r["src"], r["text"][:40])
        if key in seen:
            continue
        seen.add(key)
        parts.append(f"[{r['src']}]\n{r['text']}")
    return "\n\n".join(parts)
