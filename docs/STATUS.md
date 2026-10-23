# Implementation status

The PRD asks for a status sheet in the repository (section 22). Words used here: **implemented** means present
and tested in this repo; **deterministic** means it runs without a paid model; **not started** means no code yet.
A simulated or deterministic result never satisfies an inference, speech or streaming target.

Last updated: 2026-10-23.

## Functional requirements (PRD section 20)

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| FR01 P0 | Account and entitlement | Implemented with dev login only. Enrollment, allowance and cross-account 404s are real; production authentication is not started | `tests/test_sessions.py`, `tests/test_isolation.py` |
| FR02 P0 | Recorded lesson | Partial. Lesson metadata, version, recipe timeline, progress; frontend previews a local MP4. No hosted video, captions or transcript yet | `PUT /api/me/progress` |
| FR03 P0 | Lab launch and reset | Implemented for the server-state Content Studio (fixture load, health check, reset keeps saved work). Real browser lab not started | `tests/test_actions.py` |
| FR04 P0 | Bounded tutor tools | Implemented: schema validation, per-lesson allow list, server-scoped identity | `tests/test_actions.py` |
| FR05 P0 | Live session lifecycle | Implemented for text turns: create, state, Stop, control, end, time cap, idle expiry. Push-to-talk and media not started | `tests/test_sessions.py`, `tests/test_stop.py` |
| FR06 P0 | Observation and verification | Implemented: success only after the new state is re-read and checked | `test_unverified_action_is_not_reported_as_success` |
| FR07 P0 | Assessment | Implemented for the L03 rule-based checklist with evidence, revise and appeal. Model-assisted rubric and reviewer queue not started | `tests/test_memory_and_assessment.py` |
| FR08 P0 | Memory | Implemented: structured summary on end, view, delete one, reset, opt-out, isolation | `tests/test_memory_and_assessment.py` |
| FR09 P0 | Usage and cleanup | Implemented: per-session duration, tokens, actions, allowance settlement, token budget stop, lab disposal | `tests/test_sessions.py` |
| FR10 P1 | Course administration | Not started (content is versioned files; no admin UI) | |
| FR11 P1 | Payments and invoices | Not started | |
| FR12 P1 | Community and cohort | Not started | |
| FR13 P2 | Multiple subjects and presenters | Structure ready (course packages, recipes, manifests); one course loaded | `content/README.md` |
| FR14 P2 | Organisation accounts | Not started (`organisation_id` column reserved) | |

## Acceptance gates (PRD section 23)

| Test | Target | Status |
|---|---|---|
| Arabic understanding | 18/20 utterances | Not measurable yet (no speech recognition) |
| Grounded answer | 9/10 with valid sources | Deterministic retrieval passes 10/10 on the draft eval set (`tests/test_grounding.py`). Re-run in Gemini mode and after founder review of the passages |
| Lab completion | 18/20 runs reach saved state | Deterministic path tested; needs the real model and browser lab with slow-network and failing-tool runs |
| Warm response latency | median ≤5 s, p95 ≤10 s to first audio | Not measurable yet (no audio) |
| Streaming | 25 fps for 15 min, A/V skew ≤200 ms | Not started |
| Stop | ≤700 ms audio/video stop; stale tools do not commit | Epoch logic implemented and tested (`tests/test_stop.py`); media stop not started |
| Isolation | no A data for B | Implemented and tested across sessions, events, turns, actions, artifacts, exports, submissions and memory |
| Recovery | honest error, work preserved | Provider failure and budget stop tested; worker kill / network loss not started |
| Cost and cleanup | resources expire, costs reconcile | Session usage recorded; provider invoice reconciliation not started |
| Learning | changed task with less help | Needs a cohort |

## Build phases (PRD section 24)

| Phase | Scope | Status |
|---|---|---|
| A | Task, character design, fixture, passages, rubric, prototype flow | Fixture, passages (draft), rubric and UI flow in repo. Character design and passage review are founder tasks |
| B | Real browser lab, demonstration capture, narration, own human video | Not started. See `SETUP.md` step 2 |
| C | Backend, model, tools, memory and events connected to the frontend | Backend and frontend connected in deterministic mode; Gemini adapter implemented and tested with a fake client, not yet run with a real key |
| D | ASR, Arabic TTS, LiveKit, streaming face worker | Not started. See `SETUP.md` step 3 |
| E | Full first course and small cohort | Not started |
| F | Payments, hosting, compliance, observability, second course | Not started |

## Next actions

1. Run the backend and frontend locally (`SETUP.md` step 1) and complete the L03 lab once yourself.
2. Review and edit the 17 Arabic passages in `content/ai-for-everyone/passages/L03.ar.json`; set `reviewed_at`.
3. Add a Gemini key and re-run the grounding eval and the lab flow in `gemini` mode.
4. Add the Playwright browser lab adapter behind the same tool manifest.
5. Produce the eight-minute recorded L03 lesson (Phase B).

## Known follow-ups

- Return rule checks inside `generate_draft` / `revise_draft` results so the UI does not need an extra `read_output` step.
- Add a server-sent event stream for session events (PRD section 21) to replace the frontend's 1.5 s polling.
- Add `GET /api/me/sessions/active` so the UI can resume without relying on the `409 session_active` response.
- Frontend has no automated test suite yet; the browser flow was checked manually with Playwright.
