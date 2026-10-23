# 4weeks.ai backend starter

FastAPI tutor coordinator for the first lesson proof (PRD v2, sections 5, 10–13, 20–23). This README is the
authoritative list of what is implemented.

## Run it

```bash
cd backend
uv venv --python 3.12            # or: python3.12 -m venv .venv
uv pip install -e ".[dev]"        # or: .venv/bin/pip install -e ".[dev]"
cp .env.example .env              # optional; defaults are deterministic mode
.venv/bin/pytest                  # 56 tests, no network, no paid inference
.venv/bin/uvicorn app.main:create_app --factory --reload --port 8000
```

Open <http://localhost:8000/docs> for the interactive API.

### Modes

| `FOURWEEKS_MODE` | Lab drafts | Tutor reasoning | Cost |
|---|---|---|---|
| `deterministic` (default) | Template drafts built from fixture sentences; a weak prompt really produces a long draft with an invented offer | Rule-based stand-in with the same tool/observation loop | None |
| `gemini` | Real model output | Gemini function calling with validated, observed tools | Gemini API usage |

To switch to real model drafts: `uv pip install -e ".[gemini]"`, put `GEMINI_API_KEY=...` and
`FOURWEEKS_MODE=gemini` in `backend/.env`, restart. The key stays on the server. Every response reports the mode
(`GET /api/health`, `session.mode`, `draft.model`) so the UI can label what is real.

## Implemented routes (all under `/api`)

| Method and path | Purpose |
|---|---|
| `GET /health` | Status, version, mode, model |
| `GET /tools` | Tool manifest with parameter schemas |
| `POST /dev/learners` | Local dev login: creates a learner, a bearer token and enrollments. Disabled by `FOURWEEKS_DEV_AUTH=false` |
| `GET /me`, `PATCH /me` | Profile and preferences: `language`, `explanation_pref` (`short`/`detailed`), `memory_enabled` |
| `GET /me/enrollments` | Entitlement and live allowance (seconds) |
| `GET /courses`, `GET /courses/{course}` | Catalogue and four-week outline |
| `GET /courses/{course}/lessons/{lesson}` | Lesson detail, recipe timeline, rubric, lesson sections (requires enrollment) |
| `GET /me/progress`, `PUT /me/progress/{course}/{lesson}` | Lesson progress, recorded with the lesson version |
| `POST /sessions` | Entitlement + allowance check, provision lab, health check. One active session per learner (`409 session_active` returns its id) |
| `GET /sessions/{id}/state` | State, epoch, control holder, remaining seconds, lab state and version, usage |
| `GET /sessions/{id}/events?after=N` | Ordered events: `session_id`, `seq`, `turn_id`, `epoch`, `type`, payload |
| `GET /sessions/{id}/turns` | Learner messages, tutor answers and their sources |
| `POST /sessions/{id}/messages` | `{text, epoch}` → one tutor turn: retrieval, tool actions, answer, sources |
| `POST /sessions/{id}/actions` | `{tool, args, epoch, idempotency_key}` → learner lab action with the action contract |
| `POST /sessions/{id}/control` | `{holder: "learner" \| "tutor"}`; taking control also stops the tutor |
| `POST /sessions/{id}/stop` | Advance the epoch now; late model results and queued tools are discarded |
| `POST /sessions/{id}/end` | Settle usage, write learner memory (if enabled), dispose the lab |
| `GET /me/memory`, `DELETE /me/memory/{id}`, `DELETE /me/memory` | View, delete one, reset all |
| `GET /me/artifacts`, `GET /me/artifacts/{id}` | Saved work (only the owner's) |
| `GET /me/artifacts/{id}/export` | Markdown download with prompt, draft, model, fixture version, hash and checks |
| `POST /me/artifacts/{id}/submissions` | Rule-based rubric checks with per-criterion evidence |
| `GET /me/submissions`, `GET /me/submissions/{id}`, `POST /me/submissions/{id}/appeal` | Results and appeal |

Errors are `{"error": {"code": "...", "message": "...", ...}}`. Another learner's ids always return `404`.

### Action contract

Every lab action returns `action_id, tool, actor, status (succeeded|failed|rejected|stale), observed_state_version,
result, screenshot_ref, duration_ms, error_category, error_message, replayed`. A step is `succeeded` only after the
new lab state is re-read and the expected change is observed.

### Tools (Content Studio)

`open_lab, read_lab_state, set_brief, set_audience, set_tone, set_prompt, generate_draft, revise_draft,
read_output, save_draft, reset_lab`. No shell, code execution, navigation or database access is exposed. The
learner must take control to edit; reading and saving never need control. The tutor never acts while the
learner holds control.

## Layout

```
app/
  main.py            app factory (indexes course passages on startup)
  api.py             HTTP routes
  sessions.py        lifecycle, epochs, Stop, control, expiry, usage, the action path
  tutor.py           turn loop: retrieve → model step → validated tools → observe → answer
  lab/tools.py       bounded tool manifest and argument validation
  lab/content_studio.py  lab state machine: prepare (may call the model) → commit → verify
  llm/deterministic.py   template generator + rule-based tutor (no network)
  llm/gemini.py      Gemini adapter (optional dependency)
  retrieval.py       SQLite FTS5 over approved passages, Arabic normalization
  checks.py          prompt/draft heuristics shared by the generator and assessment
  memory.py          learner memory summaries
  artifacts.py       saved work, export, submissions, appeal
  schema.sql         SQLite schema
tests/               56 tests: lifecycle, Stop, isolation, idempotency, verification, grounding, memory, assessment
```

Course content is read from `../content/<course_id>/` (see `content/README.md`).

## Not in this starter yet

Speech recognition, Arabic speech synthesis, LiveKit transport, the avatar worker, a real browser lab
(Playwright), production authentication, payments and hosting. See `../docs/STATUS.md`.
