import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from agent import run
from tools.audio import ext_audio
from tools.ocr import ext_img
from tools.pdf import ext_pdf

load_dotenv()

app = FastAPI(title="ParallelMinds")

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
    return {"status": "ok"}


@app.post("/api/process")
async def process(query: str = Form(default=""), files: list[UploadFile] = File(default=[])):
    extracted = []
    for file in files:
        extracted.append(await parse_file(file))

    types = [e["type"] for e in extracted]
    if query.strip():
        types.append("text")

    return run(query, types, extracted)


async def parse_file(file: UploadFile) -> dict:
    data = await file.read()
    name = file.filename or "file"
    mime = file.content_type or ""

    if mime == "application/pdf" or name.lower().endswith(".pdf"):
        out = ext_pdf(data)
        item = {"type": "pdf", "name": name, "text": out.get("text", "")}
        if out.get("urls"):
            item["urls"] = out["urls"]
        if out.get("error"):
            item["error"] = out["error"]
        return item

    if mime.startswith("image/") or name.lower().endswith((".jpg", ".jpeg", ".png")):
        img_mime = mime if mime.startswith("image/") else "image/jpeg"
        out = ext_img(data, img_mime)
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
