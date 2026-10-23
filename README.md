# 4weeks.ai

Arabic-first practical AI course with an AI instructor and a live tutor that works in a real lab.
The first product is **AI for Everyone**: 20 lessons over four weeks, ending in an assessed portfolio project.

The full plan is in [`docs/prd/4weeks_AI_PRD_v2.pdf`](docs/prd/4weeks_AI_PRD_v2.pdf). This branch builds the first
engineering proof from it: lesson L03 ("Write a clear prompt") where the tutor answers a course question,
operates the Content Studio lab, verifies its output, accepts an interruption and hands control back.

## Quick start

You need Python (via `uv`) and Node.js 22. Full list and later downloads: [`docs/SETUP.md`](docs/SETUP.md).

```bash
# terminal 1: backend
cd backend
uv venv --python 3.12 && uv pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/uvicorn app.main:create_app --factory --reload --port 8000

# terminal 2: frontend
cd frontend
npm install
npm run dev          # http://localhost:5173
```

It starts in **deterministic mode**: real sessions, Stop, tools, memory and checks, with template drafts instead
of a paid model. Add a Gemini key to switch to real model output (`backend/README.md`).

## Repository layout

| Path | What it is |
|---|---|
| `backend/` | FastAPI tutor coordinator: sessions, epochs and Stop, bounded lab tools, retrieval, memory, assessment |
| `frontend/` | React + TypeScript + Vite app, Arabic (RTL) by default with English |
| `content/` | Versioned course packages: course outline, lesson recipe, fixtures, rubrics, Arabic passages, eval set |
| `docs/SETUP.md` | What to download for each build phase |
| `docs/STATUS.md` | Implementation status against the PRD requirements and acceptance gates |
| `docs/prd/` | Product requirements, version 2 |

## Architecture (PRD section 5)

```
Learner workspace (frontend) ──commands──▶ Tutor coordinator (FastAPI)
                                              │ retrieve          │ tools (validated, observed)
                                              ▼                   ▼
                                  Course + learner data     Content Studio lab
                                  (SQLite: passages FTS,    (server state now,
                                   memory, artifacts)        Playwright browser next)
                                              │
                                              ▼
                                  Model adapter: deterministic | Gemini
Not built yet: speech (whisper.cpp), Arabic voice (Chatterbox), LiveKit transport, MuseTalk avatar worker.
```

Each piece is separate so it can be tested and replaced: the screen the learner sees, what the model reads,
and what the model is allowed to do are three different things.
