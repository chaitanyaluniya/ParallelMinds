# ParallelMinds

Multi-modal agent for the DSAI Assignment (June 2026). Accepts text, images, PDFs, and audio; classifies intent; chains tools; returns text-only answers.

## Structure

```
ParallelMinds/
├── backend/
│   ├── main.py          # FastAPI app
│   ├── agent.py         # Intent + tool routing
│   └── tools/           # pdf, ocr, audio, youtube, etc.
├── frontend/            # React + Vite (Phase 5)
├── tests/
├── Dockerfile
└── render.yaml
```

## Local setup

```bash
cd ParallelMinds
python -m venv .venv
source .venv/bin/activate

pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
# add GOOGLE_API_KEY to backend/.env

cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Health check: http://localhost:8000/health

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes (Phase 2+) | Gemini API key |
| `GEMINI_MODEL` | No | Default: `gemini-2.0-flash` |
| `CORS_ORIGINS` | No | Comma-separated frontend URLs |

## Status

- [x] Project structure
- [x] FastAPI + `/health` + CORS
- [ ] Extraction tools (PDF, OCR, audio, YouTube)
- [ ] Agent brain
- [ ] `/api/process` endpoint
- [ ] React frontend
- [ ] Deploy
