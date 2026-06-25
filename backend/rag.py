import numpy as np
from fastembed import TextEmbedding

CHUNK = 900
OVERLAP = 120
TOP = 3
MIN_CHARS = 2500  # skip rag for short notes

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
        _emb = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _emb


def embed(texts):
    return list(get_emb().embed(texts))


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
        r["vec"] = np.array(v, dtype=np.float32)
    _buckets[sid] = rows


def search(sid, query, k=TOP):
    rows = _buckets.get(sid) or []
    if not rows or not query.strip():
        return ""
    qv = np.array(list(embed([query.strip()]))[0], dtype=np.float32)
    scored = []
    for r in rows:
        v = r["vec"]
        sim = float(np.dot(qv, v) / (np.linalg.norm(qv) * np.linalg.norm(v) + 1e-9))
        scored.append((sim, r))
    scored.sort(key=lambda x: -x[0])
    parts = []
    for _, r in scored[:k]:
        parts.append(f"[{r['src']}]\n{r['text']}")
    return "\n\n".join(parts)
