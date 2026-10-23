# 4weeks.ai frontend

React 19 + TypeScript + Vite. Arabic first (RTL), with an English toggle. Plain CSS, no UI framework.

## Run

```bash
# 1. backend (from the repository root, in another terminal)
cd backend && .venv/bin/uvicorn app.main:create_app --factory --reload --port 8000

# 2. frontend
cd frontend
npm install
npm run dev          # http://localhost:5173  (proxies /api to http://localhost:8000)
```

```bash
npm run build        # type-check (tsc) + production build into dist/
npm run typecheck    # type-check only
```

On first load the app calls `POST /api/dev/learners` and keeps the dev token in `localStorage`
(`fourweeks.token`). Clear site data to start as a new learner. Dev login only works while the backend runs
with `FOURWEEKS_DEV_AUTH=true`.

## Screens

| Route | Screen |
|---|---|
| `#/dashboard` | Course, weekly outcomes, progress, live minutes left, recent work |
| `#/course`, `#/course/L03` | Outline (4 weeks × 5 lessons), lesson detail, local MP4 preview, progress |
| `#/live/L03` | Live tutor room: instructor area, Content Studio lab, Stop / Take control / End, transcript with sources and lab steps |
| `#/work`, `#/work/<artifact_id>` | Saved work, Markdown export, rule-based checks, appeal |
| `#/settings` | Language, explanation style, memory consent, view/delete memory |

## What is real and what is a placeholder

Real (talks to the backend): learner session, session lifecycle and epochs, Stop, control hand-over, every
lab field and button (typed tool actions with idempotency keys), observed action results, retrieval sources,
saved artifacts, export, submissions, appeals, memory and preferences.

Behaviour depends on the backend mode, shown in the badge at the top of every screen:
*Deterministic test mode* uses template drafts and a rule-based tutor; real model mode uses the model
configured on the server.

Placeholders, labelled in the UI:

- The instructor area is a neutral figure. Voice, captions and the face video pipeline are not connected.
- Messages are typed. Push-to-talk comes with the speech pipeline.
- The recorded-lesson player only previews a local MP4 chosen by the learner; nothing is uploaded and no
  final lesson video exists yet.
- Lesson outcomes and acceptance text are the PRD's English text until the Arabic versions are written.
