import sqlite3
from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse

from . import __version__, artifacts, auth, clock, db, memory
from .db import tx
from .errors import ApiError, not_found
from .lab.tools import manifest
from .schemas import (
    ActionIn,
    AppealIn,
    ControlIn,
    CreateSessionIn,
    DevLearnerIn,
    MessageIn,
    PreferencesIn,
    ProgressIn,
)
from .services import Services
from .sessions import SessionService
from .tutor import TutorCoordinator

router = APIRouter(prefix="/api")


def get_services(request: Request) -> Services:
    return request.app.state.services


def get_conn(services: Services = Depends(get_services)) -> Iterator[sqlite3.Connection]:
    conn = db.connect(services.settings.db_path)
    try:
        yield conn
    finally:
        conn.close()


def get_learner(request: Request, conn: sqlite3.Connection = Depends(get_conn)) -> sqlite3.Row:
    return auth.learner_from_request(conn, request)


def _me(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "learner_id": row["learner_id"],
        "display_name": row["display_name"],
        "language": row["language"],
        "explanation_pref": row["explanation_pref"],
        "memory_enabled": bool(row["memory_enabled"]),
    }


# ---------------------------------------------------------------- service info


@router.get("/health")
def health(services: Services = Depends(get_services)) -> dict[str, Any]:
    return {
        "status": "ok",
        "version": __version__,
        "mode": services.settings.mode,
        "model": services.settings.gemini_model if services.settings.mode == "gemini" else "deterministic",
        "dev_auth": services.settings.dev_auth,
    }


@router.get("/tools")
def tools() -> list[dict[str, Any]]:
    return manifest()


# ---------------------------------------------------------------- learner


@router.post("/dev/learners", status_code=201)
def dev_learner(
    body: DevLearnerIn, services: Services = Depends(get_services), conn: sqlite3.Connection = Depends(get_conn)
) -> dict[str, Any]:
    if not services.settings.dev_auth:
        raise ApiError(404, "not_found", "Dev login is disabled")
    learner_id, token = auth.create_dev_learner(conn, services.settings, services.registry, body.display_name, body.language)
    return {"learner_id": learner_id, "token": token}


@router.get("/me")
def me(learner: sqlite3.Row = Depends(get_learner)) -> dict[str, Any]:
    return _me(learner)


@router.patch("/me")
def update_me(
    body: PreferencesIn, learner: sqlite3.Row = Depends(get_learner), conn: sqlite3.Connection = Depends(get_conn)
) -> dict[str, Any]:
    changes = body.model_dump(exclude_none=True)
    if changes:
        with tx(conn):
            conn.execute(
                f"UPDATE learners SET {', '.join(f'{k} = ?' for k in changes)} WHERE learner_id = ?",
                (*[int(v) if isinstance(v, bool) else v for v in changes.values()], learner["learner_id"]),
            )
    return _me(conn.execute("SELECT * FROM learners WHERE learner_id = ?", (learner["learner_id"],)).fetchone())


@router.get("/me/enrollments")
def enrollments(learner: sqlite3.Row = Depends(get_learner), conn: sqlite3.Connection = Depends(get_conn)):
    rows = conn.execute("SELECT * FROM enrollments WHERE learner_id = ?", (learner["learner_id"],))
    return [
        {
            "course_id": r["course_id"],
            "status": r["status"],
            "expires_at": r["expires_at"],
            "live_allowance_seconds": r["live_allowance_seconds"],
            "live_used_seconds": r["live_used_seconds"],
            "live_remaining_seconds": max(0, r["live_allowance_seconds"] - r["live_used_seconds"]),
        }
        for r in rows
    ]


# ---------------------------------------------------------------- courses


@router.get("/courses")
def courses(services: Services = Depends(get_services)) -> list[dict[str, Any]]:
    return [
        {"course_id": c.course_id, "version": c.version, "title": c.data["title"], "lessons": len(c.lessons)}
        for c in services.registry.courses.values()
    ]


@router.get("/courses/{course_id}")
def course_outline(course_id: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    course = services.registry.course(course_id)
    if course is None:
        raise not_found("Course")
    return {
        "course_id": course.course_id,
        "version": course.version,
        "title": course.data["title"],
        "brief": course.data["brief"],
        "release": course.data["release"],
        "weeks": [
            {
                **week,
                "lessons": [
                    {
                        "lesson_id": lesson["lesson_id"],
                        "version": lesson["version"],
                        "title": lesson["title"],
                        "outcome": lesson["outcome"],
                        "has_lab": lesson["lesson_id"] in course.recipes,
                    }
                    for lesson in course.data["lessons"]
                    if lesson["week"] == week["week"]
                ],
            }
            for week in course.data["weeks"]
        ],
    }


@router.get("/courses/{course_id}/lessons/{lesson_id}")
def lesson_detail(
    course_id: str,
    lesson_id: str,
    services: Services = Depends(get_services),
    learner: sqlite3.Row = Depends(get_learner),
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict[str, Any]:
    course = services.registry.course(course_id)
    lesson = course.lesson(lesson_id) if course else None
    if lesson is None:
        raise not_found("Lesson")
    enrolled = conn.execute(
        "SELECT 1 FROM enrollments WHERE learner_id = ? AND course_id = ? AND status = 'active'",
        (learner["learner_id"], course_id),
    ).fetchone()
    if not enrolled:
        raise ApiError(403, "not_entitled", "No active enrollment for this course")
    recipe = course.recipe(lesson_id)
    passages = [p for p in course.passages if p["lesson_id"] == lesson_id]
    return {
        **{k: v for k, v in lesson.items() if k != "recipe"},
        "course_id": course_id,
        "course_version": course.version,
        "reviewed_at": max((p["reviewed_at"] or "" for p in passages), default="") or None,
        "recipe": None
        if recipe is None
        else {
            "recipe_version": recipe["recipe_version"],
            "outcome": recipe["outcome"],
            "timeline": recipe["timeline"],
            "fixture_id": recipe["fixture_id"],
            "practice_fixture_id": recipe.get("practice_fixture_id"),
            "rubric": course.rubrics[recipe["rubric_id"]],
            "allowed_tools": recipe["allowed_tools"],
        },
        "sections": [
            {"passage_id": p["passage_id"], "section_id": p["section_id"], "title": p["title"], "text": p["text"],
             "source_url": p["source_url"]}
            for p in passages
        ],
    }


@router.get("/me/progress")
def get_progress(learner: sqlite3.Row = Depends(get_learner), conn: sqlite3.Connection = Depends(get_conn)):
    rows = conn.execute("SELECT * FROM progress WHERE learner_id = ?", (learner["learner_id"],))
    return [{k: r[k] for k in ("course_id", "lesson_id", "lesson_version", "status", "updated_at")} for r in rows]


@router.put("/me/progress/{course_id}/{lesson_id}")
def put_progress(
    course_id: str,
    lesson_id: str,
    body: ProgressIn,
    services: Services = Depends(get_services),
    learner: sqlite3.Row = Depends(get_learner),
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict[str, Any]:
    course = services.registry.course(course_id)
    lesson = course.lesson(lesson_id) if course else None
    if lesson is None:
        raise not_found("Lesson")
    now = clock.now_iso()
    with tx(conn):
        conn.execute(
            "INSERT INTO progress (learner_id, course_id, lesson_id, lesson_version, status, updated_at)"
            " VALUES (?,?,?,?,?,?) ON CONFLICT (learner_id, course_id, lesson_id) DO UPDATE SET"
            " lesson_version = excluded.lesson_version, status = excluded.status, updated_at = excluded.updated_at",
            (learner["learner_id"], course_id, lesson_id, lesson["version"], body.status, now),
        )
    return {"course_id": course_id, "lesson_id": lesson_id, "lesson_version": lesson["version"],
            "status": body.status, "updated_at": now}


# ---------------------------------------------------------------- sessions


def _sessions(services: Services = Depends(get_services), conn: sqlite3.Connection = Depends(get_conn)) -> SessionService:
    return SessionService(conn, services)


@router.post("/sessions", status_code=201)
def create_session(
    body: CreateSessionIn, learner: sqlite3.Row = Depends(get_learner), sessions: SessionService = Depends(_sessions)
) -> dict[str, Any]:
    return sessions.create(learner, body.course_id, body.lesson_id)


@router.get("/sessions/{session_id}/state")
def session_state(
    session_id: str, learner: sqlite3.Row = Depends(get_learner), sessions: SessionService = Depends(_sessions)
) -> dict[str, Any]:
    return sessions.state(learner["learner_id"], session_id)


@router.get("/sessions/{session_id}/events")
def session_events(
    session_id: str,
    after: int = 0,
    learner: sqlite3.Row = Depends(get_learner),
    sessions: SessionService = Depends(_sessions),
) -> list[dict[str, Any]]:
    return sessions.events(learner["learner_id"], session_id, after)


@router.get("/sessions/{session_id}/turns")
def session_turns(
    session_id: str, learner: sqlite3.Row = Depends(get_learner), sessions: SessionService = Depends(_sessions)
) -> list[dict[str, Any]]:
    return TutorCoordinator(sessions).turns(learner["learner_id"], session_id)


@router.post("/sessions/{session_id}/messages")
def post_message(
    session_id: str,
    body: MessageIn,
    learner: sqlite3.Row = Depends(get_learner),
    sessions: SessionService = Depends(_sessions),
) -> dict[str, Any]:
    return TutorCoordinator(sessions).handle_message(learner, session_id, body.text, body.epoch)


@router.post("/sessions/{session_id}/actions")
def post_action(
    session_id: str,
    body: ActionIn,
    learner: sqlite3.Row = Depends(get_learner),
    sessions: SessionService = Depends(_sessions),
) -> dict[str, Any]:
    session = sessions.active_row(learner["learner_id"], session_id)
    sessions.check_epoch(session, body.epoch)
    return sessions.run_action(
        session, actor="learner", tool=body.tool, args=body.args, epoch=body.epoch, idempotency_key=body.idempotency_key
    )


@router.post("/sessions/{session_id}/control")
def post_control(
    session_id: str,
    body: ControlIn,
    learner: sqlite3.Row = Depends(get_learner),
    sessions: SessionService = Depends(_sessions),
) -> dict[str, Any]:
    return sessions.set_control(learner["learner_id"], session_id, body.holder)


@router.post("/sessions/{session_id}/stop")
def post_stop(
    session_id: str, learner: sqlite3.Row = Depends(get_learner), sessions: SessionService = Depends(_sessions)
) -> dict[str, Any]:
    return sessions.stop(learner["learner_id"], session_id)


@router.post("/sessions/{session_id}/end")
def post_end(
    session_id: str, learner: sqlite3.Row = Depends(get_learner), sessions: SessionService = Depends(_sessions)
) -> dict[str, Any]:
    return sessions.end(learner["learner_id"], session_id)


# ---------------------------------------------------------------- memory


@router.get("/me/memory")
def get_memory(learner: sqlite3.Row = Depends(get_learner), conn: sqlite3.Connection = Depends(get_conn)):
    return memory.list_memory(conn, learner["learner_id"])


@router.delete("/me/memory/{memory_id}")
def delete_memory(
    memory_id: str, learner: sqlite3.Row = Depends(get_learner), conn: sqlite3.Connection = Depends(get_conn)
) -> dict[str, Any]:
    with tx(conn):
        if not memory.delete_one(conn, learner["learner_id"], memory_id):
            raise not_found("Memory")
    return {"deleted": 1}


@router.delete("/me/memory")
def reset_memory(learner: sqlite3.Row = Depends(get_learner), conn: sqlite3.Connection = Depends(get_conn)):
    with tx(conn):
        return {"deleted": memory.delete_all(conn, learner["learner_id"])}


# ---------------------------------------------------------------- artifacts and assessment


@router.get("/me/artifacts")
def get_artifacts(learner: sqlite3.Row = Depends(get_learner), conn: sqlite3.Connection = Depends(get_conn)):
    return artifacts.list_artifacts(conn, learner["learner_id"])


@router.get("/me/artifacts/{artifact_id}")
def get_artifact(
    artifact_id: str, learner: sqlite3.Row = Depends(get_learner), conn: sqlite3.Connection = Depends(get_conn)
) -> dict[str, Any]:
    return artifacts.get_artifact(conn, learner["learner_id"], artifact_id)


@router.get("/me/artifacts/{artifact_id}/export")
def export_artifact(
    artifact_id: str, learner: sqlite3.Row = Depends(get_learner), conn: sqlite3.Connection = Depends(get_conn)
) -> PlainTextResponse:
    artifact = artifacts.get_artifact(conn, learner["learner_id"], artifact_id)
    return PlainTextResponse(
        artifacts.export_markdown(artifact),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{artifact_id}.md"'},
    )


@router.post("/me/artifacts/{artifact_id}/submissions", status_code=201)
def submit_artifact(
    artifact_id: str,
    services: Services = Depends(get_services),
    learner: sqlite3.Row = Depends(get_learner),
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict[str, Any]:
    with tx(conn):
        return artifacts.submit(conn, services.registry, learner["learner_id"], artifact_id)


@router.get("/me/submissions")
def get_submissions(learner: sqlite3.Row = Depends(get_learner), conn: sqlite3.Connection = Depends(get_conn)):
    return artifacts.list_submissions(conn, learner["learner_id"])


@router.get("/me/submissions/{submission_id}")
def get_submission(
    submission_id: str, learner: sqlite3.Row = Depends(get_learner), conn: sqlite3.Connection = Depends(get_conn)
) -> dict[str, Any]:
    return artifacts.get_submission(conn, learner["learner_id"], submission_id)


@router.post("/me/submissions/{submission_id}/appeal")
def appeal_submission(
    submission_id: str,
    body: AppealIn,
    learner: sqlite3.Row = Depends(get_learner),
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict[str, Any]:
    with tx(conn):
        return artifacts.appeal(conn, learner["learner_id"], submission_id, body.reason)
