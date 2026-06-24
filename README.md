# ParallelMinds

Multi-modal agentic application for the DSAI Assignment (June 2026). Accepts text, images, PDFs, and audio simultaneously; plans and executes multi-step tool chains autonomously; returns text-only outputs with extracted content and plan traces.

## Features (Assignment Coverage)

- **Inputs:** Text, JPG/PNG (OCR), PDF (parse + OCR fallback), Audio (MP3/WAV/M4A)
- **Agent:** Intent understanding, mandatory follow-up when ambiguous, autonomous tool chaining
- **Tasks:** OCR, PDF extraction, YouTube transcripts, summarization, sentiment, code explanation, audio transcription, cross-input reasoning
- **UI:** Chat-like interface with file upload, extracted text panel, plan trace
- **Deployment:** Docker + Render config included

## Project Structure

```
ParallelMinds/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Environment settings
│   ├── api/routes/             # /api/chat, /api/health
│   ├── agent/                  # Orchestrator + planner
│   ├── ingest/                 # Multi-input pipeline
│   ├── tools/                  # Tool registry + implementations
│   ├── models/                 # Pydantic schemas
│   └── static/                 # Chat UI (HTML/CSS/JS)
├── tests/                      # pytest test suite
├── docs/architecture.md        # Architecture diagram
├── Dockerfile
├── render.yaml                 # Render deployment config
├── requirements.txt
└── .env.example
```

## Setup

### Prerequisites

- Python 3.11+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (for image/scanned PDF OCR)
- [Poppler](https://poppler.freedesktop.org/) (for PDF rendering)
- [FFmpeg](https://ffmpeg.org/) (for audio processing)

### Local Development

```bash
# Clone and enter project
cd ParallelMinds

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set OPENAI_API_KEY

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 for the chat UI.

### Docker

```bash
docker build -t parallelminds .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... parallelminds
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for agent planning & generation |
| `OPENAI_MODEL` | No | Default: `gpt-4o-mini` |
| `WHISPER_MODEL` | No | Whisper size: `tiny`, `base`, `small`, etc. |
| `PORT` | No | Server port (default 8000) |

## API

### `POST /api/chat`

Multipart form data:

- `query` (string): User text query
- `files` (file[], optional): Image, PDF, or audio files

Returns JSON with `extracted_contents`, `plan_trace`, `final_answer`, and optional `clarification_question`.

### `GET /api/health`

Health check for deployment probes.

## Testing

```bash
pytest
```

## Deployment (Render)

1. Push repo to GitHub
2. Connect to Render; use `render.yaml` blueprint or manual Docker deploy
3. Set `OPENAI_API_KEY` in Render environment
4. Submit live URL with assignment

## Implementation Status

This skeleton provides modular structure, API routes, tool registry, UI, tests, and deployment config. Individual tools and LLM-powered planning are stubbed and marked `TODO` for the next implementation phase.

## Design Decisions

- **FastAPI + static frontend** — Simple deployment, no separate frontend build step
- **Tool registry pattern** — Each assignment task maps to one tool; planner chains them
- **Pydantic schemas** — Typed request/response models for API and UI contract
- **Clarification-first planner** — Never guesses when intent is ambiguous (assignment rule)

See [docs/architecture.md](docs/architecture.md) for the full architecture diagram.
