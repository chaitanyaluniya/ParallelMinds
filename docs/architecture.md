# Architecture — ParallelMinds Agent

## Overview

ParallelMinds is a multi-modal agentic application that accepts text, images, PDFs, and audio in a single request, understands user intent, and autonomously chains tools to produce text-only outputs.

## Component Diagram

```mermaid
flowchart TB
    subgraph UI["Frontend (Static HTML/JS)"]
        ChatInput[Text Input + File Upload]
        OutputPanel[Chat Output]
        ExtractedPanel[Extracted Text Panel]
        PlanPanel[Plan Trace Panel]
    end

    subgraph API["FastAPI Backend"]
        ChatRoute["POST /api/chat"]
        HealthRoute["GET /api/health"]
    end

    subgraph Ingest["Input Pipeline"]
        Validator[File Validator]
        TextExtract[Text Handler]
        ImageOCR[Image OCR]
        PDFParse[PDF Parser + OCR Fallback]
        AudioSTT[Audio Speech-to-Text]
    end

    subgraph Agent["Agent Core"]
        Planner[Intent Planner]
        Orchestrator[Orchestrator]
        Synthesizer[Answer Synthesizer]
    end

    subgraph Tools["Tool Registry"]
        T1[ocr_extract]
        T2[pdf_extract]
        T3[audio_transcribe]
        T4[youtube_transcript]
        T5[summarize]
        T6[sentiment_analysis]
        T7[code_explain]
        T8[conversational_answer]
        T9[cross_input_compare]
    end

    ChatInput --> ChatRoute
    ChatRoute --> Validator
    Validator --> TextExtract
    Validator --> ImageOCR
    Validator --> PDFParse
    Validator --> AudioSTT
    TextExtract --> Orchestrator
    ImageOCR --> Orchestrator
    PDFParse --> Orchestrator
    AudioSTT --> Orchestrator
    Orchestrator --> Planner
    Planner --> Tools
    Tools --> Synthesizer
    Synthesizer --> OutputPanel
    Orchestrator --> ExtractedPanel
    Orchestrator --> PlanPanel
```

## Data Flow

1. **Ingest** — User submits query + files via `/api/chat`
2. **Extract** — Pipeline extracts/transcribes all inputs into `ExtractedContent` objects
3. **Plan** — Planner detects intent; asks clarification if ambiguous
4. **Execute** — Orchestrator runs minimal tool chain from registry
5. **Respond** — Synthesizer produces final text answer + plan trace for UI

## Directory Structure

```
app/
├── main.py              # FastAPI entry
├── config.py            # Settings
├── api/routes/          # HTTP endpoints
├── agent/               # Planner + orchestrator
├── ingest/              # Multi-input extraction
├── tools/               # Tool implementations
├── models/              # Pydantic schemas
└── static/              # Chat UI
tests/                   # pytest suite
docs/                    # Architecture & design
```

## Assignment Task Mapping

| Assignment Task | Tool / Module |
|-----------------|---------------|
| Image/PDF OCR | `tools/ocr.py`, `tools/pdf_parser.py` |
| YouTube transcript | `tools/youtube.py` |
| Summarization | `tools/summarizer.py` |
| Sentiment | `tools/sentiment.py` |
| Code explanation | `tools/code_explainer.py` |
| Audio transcription | `tools/audio_transcribe.py` |
| Cross-input reasoning | `tools/cross_input.py` |
| Follow-up questions | `agent/planner.py` |
| Plan trace in UI | `static/js/app.js` + `models/schemas.py` |
