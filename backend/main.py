import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from agent import run, run_live
from cost import estimate
from limits import MAX_FILE
from llm import reset as reset_usage
from mem import clear_pend, ctx as hist_ctx, get_pend
from tools.audio import ext_audio
from tools.ocr import ext_img
from tools.pdf import ext_pdf

load_dotenv()

app = FastAPI(title="ParallelMinds")
MAX_MB = MAX_FILE // (1024 * 1024)
WEB_DIR = Path(__file__).resolve().parent / "web"

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "max_file_mb": MAX_MB}


@app.post("/api/estimate")
async def est(
    query: str = Form(default=""),
    files_meta: str = Form(default="[]"),
    session_id: str = Form(default=""),
):
    try:
        meta = json.loads(files_meta)
    except json.JSONDecodeError:
        meta = []

    for f in meta:
        if f.get("size", 0) > MAX_FILE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {MAX_MB}MB): {f.get('name', 'file')}",
            )

    types = types_from(meta, query)
    return estimate(query, types, meta, hist_ctx(session_id))


@app.post("/api/process")
async def process(
    query: str = Form(default=""),
    files: list[UploadFile] = File(default=[]),
    session_id: str = Form(default=""),
):
    reset_usage()
    extracted = await load_files(files, query, session_id)
    types = mk_types(extracted, query)
    return run(query, types, extracted, session_id)


@app.post("/api/stream")
async def stream(
    query: str = Form(default=""),
    files: list[UploadFile] = File(default=[]),
    session_id: str = Form(default=""),
):
    reset_usage()
    extracted = await load_files(files, query, session_id)
    types = mk_types(extracted, query)

    def events():
        for ev in run_live(query, types, extracted, session_id):
            yield f"data: {json.dumps(ev)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


async def load_files(files, query: str, sid: str) -> list[dict]:
    extracted = []
    for file in files:
        extracted.append(await parse_file(file))

    if extracted and query.strip():
        clear_pend(sid)
        return extracted

    if not extracted and query.strip():
        pending = get_pend(sid)
        if pending:
            return pending

    return extracted


def mk_types(extracted: list[dict], query: str) -> list[str]:
    types = [e["type"] for e in extracted]
    if query.strip():
        types.append("text")
    return types


def types_from(meta: list[dict], query: str) -> list[str]:
    types = []
    for f in meta:
        mime = f.get("type") or ""
        name = (f.get("name") or "").lower()
        if mime == "application/pdf" or name.endswith(".pdf"):
            types.append("pdf")
        elif mime.startswith("image/") or name.endswith((".jpg", ".jpeg", ".png")):
            types.append("image")
        elif mime.startswith("audio/") or name.endswith((".mp3", ".wav", ".m4a")):
            types.append("audio")
    if query.strip():
        types.append("text")
    return types


async def parse_file(file: UploadFile) -> dict:
    data = await file.read()
    name = file.filename or "file"

    if len(data) > MAX_FILE:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_MB}MB): {name}")

    mime = file.content_type or ""

    if mime == "application/pdf" or name.lower().endswith(".pdf"):
        out = ext_pdf(data)
        item = {"type": "pdf", "name": name, "text": out.get("text", "")}
        if out.get("urls"):
            item["urls"] = out["urls"]
        if out.get("error"):
            item["error"] = out["error"]
        return item

    if mime.startswith("image/") or name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        img_mime = mime if mime.startswith("image/") else "image/jpeg"
        out = ext_img(data, img_mime, name)
        item = {"type": "image", "name": name, "text": out.get("text", "")}
        if out.get("confidence"):
            item["confidence"] = out["confidence"]
        if out.get("error"):
            item["error"] = out["error"]
        return item

    if mime.startswith("audio/") or name.lower().endswith((".mp3", ".wav", ".m4a")):
        out = ext_audio(data, name)
        item = {"type": "audio", "name": name, "text": out.get("text", "")}
        if out.get("duration") is not None:
            item["duration"] = out["duration"]
        if out.get("error"):
            item["error"] = out["error"]
        return item

    raise HTTPException(status_code=400, detail=f"Unsupported file type: {name}")


if WEB_DIR.exists():
    assets = WEB_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/")
    def web_root():
        return FileResponse(str(WEB_DIR / "index.html"))

    @app.get("/{path:path}")
    def web_app(path: str):
        if path.startswith("api/") or path == "health":
            raise HTTPException(status_code=404, detail="Not found")

        file_path = WEB_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(WEB_DIR / "index.html"))
