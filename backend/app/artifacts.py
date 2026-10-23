"""Learner artifacts, submissions and rule-based assessment (PRD sections 13 and 21)."""

import hashlib
import sqlite3
from typing import Any

from . import checks, clock
from .content import ContentRegistry
from .db import dumps, loads
from .errors import ApiError, not_found
from .ids import new_id
from .lab.content_studio import ContentStudio


def _artifact_dict(row: sqlite3.Row, with_content: bool = True) -> dict[str, Any]:
    data = {
        k: row[k]
        for k in ("artifact_id", "session_id", "course_id", "lesson_id", "kind", "title", "content_hash", "created_at")
    }
    if with_content:
        data["content"] = loads(row["content_json"])
    return data


def save_lab_draft(
    conn: sqlite3.Connection,
    learner_id: str,
    session: sqlite3.Row,
    studio: ContentStudio,
    draft: dict[str, Any],
    title: str | None,
    note: str | None,
) -> tuple[dict[str, Any], bool]:
    """Call inside a write transaction. Saving the same work twice returns the existing artifact."""
    content = {
        "prompt": draft.get("prompt", ""),
        "draft_text": draft["text"],
        "model": draft["model"],
        "draft_id": draft["draft_id"],
        "draft_number": draft.get("number"),
        "created_by": draft.get("created_by"),
        "generated_at": draft["created_at"],
        "fixture_id": draft["fixture_id"],
        "fixture_version": draft["fixture_version"],
        "course_version": session["course_version"],
        "checks": studio.checks_for(draft),
        "note": note,
    }
    content_hash = hashlib.sha256(
        dumps({k: content[k] for k in ("prompt", "draft_text", "model", "fixture_id", "fixture_version")}).encode()
    ).hexdigest()
    existing = conn.execute(
        "SELECT * FROM artifacts WHERE learner_id = ? AND content_hash = ?", (learner_id, content_hash)
    ).fetchone()
    if existing is not None:
        return _artifact_dict(existing, with_content=False), True
    business = studio.fixture(draft["fixture_id"]).business_name("ar")
    row = {
        "artifact_id": new_id("art"),
        "learner_id": learner_id,
        "session_id": session["session_id"],
        "course_id": session["course_id"],
        "lesson_id": session["lesson_id"],
        "kind": "lab_draft",
        "title": title or f"{business} — مسودة {draft.get('number', '')}".strip(),
        "content_json": dumps(content),
        "content_hash": content_hash,
        "created_at": clock.now_iso(),
    }
    conn.execute(
        f"INSERT INTO artifacts ({', '.join(row)}) VALUES ({', '.join('?' for _ in row)})", tuple(row.values())
    )
    return {k: v for k, v in row.items() if k not in ("learner_id", "content_json")}, False


def artifact_exists(conn: sqlite3.Connection, learner_id: str, artifact_id: str, content_hash: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM artifacts WHERE artifact_id = ? AND learner_id = ? AND content_hash = ?",
            (artifact_id, learner_id, content_hash),
        ).fetchone()
        is not None
    )


def list_artifacts(conn: sqlite3.Connection, learner_id: str) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM artifacts WHERE learner_id = ? ORDER BY created_at DESC", (learner_id,))
    return [_artifact_dict(r, with_content=False) for r in rows]


def get_artifact(conn: sqlite3.Connection, learner_id: str, artifact_id: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM artifacts WHERE artifact_id = ? AND learner_id = ?", (artifact_id, learner_id)
    ).fetchone()
    if row is None:
        raise not_found("Artifact")
    return _artifact_dict(row)


def export_markdown(artifact: dict[str, Any]) -> str:
    c = artifact["content"]
    d = c["checks"]["draft_checks"]
    return "\n".join(
        [
            f"# {artifact['title']}",
            "",
            f"- Lesson: {artifact['lesson_id']} (course {artifact['course_id']} v{c['course_version']})",
            f"- Fixture: {c['fixture_id']} v{c['fixture_version']}",
            f"- Model: {c['model']}",
            f"- Generated: {c['generated_at']}",
            f"- Saved: {artifact['created_at']}",
            f"- Content hash: {artifact['content_hash']}",
            "",
            "## Prompt",
            "",
            c["prompt"],
            "",
            "## Draft",
            "",
            c["draft_text"],
            "",
            "## Rule-based checks",
            "",
            f"- Words: {d['word_count']} / {d['max_words']}",
            f"- Call to action: {'yes' if d['has_cta'] else 'no'}",
            f"- Unsupported numbers or offers: {', '.join(d['unsupported_numbers'] + d['offer_terms']) or 'none'}",
            "",
            *([f"## Note\n\n{c['note']}", ""] if c.get("note") else []),
        ]
    )


def _criteria_results(rubric: dict[str, Any], p: checks.PromptAnalysis, d: checks.DraftAnalysis) -> list[dict]:
    def element(found: bool) -> str:
        return "found in prompt" if found else "missing from prompt"

    unsupported = d.unsupported_numbers + d.offer_terms
    outcomes = {
        "prompt_task": (p.task, element(p.task)),
        "prompt_context": (p.context and p.audience, f"context {element(p.context)}; audience {element(p.audience)}"),
        "prompt_constraints": (p.constraints, element(p.constraints)),
        "prompt_output_format": (p.output_format, element(p.output_format)),
        "draft_length": (d.within_limit, f"{d.word_count} words, limit {d.max_words}"),
        "draft_call_to_action": (d.has_cta, "call to action found" if d.has_cta else "no call to action found"),
        "draft_no_unsupported_claims": (not unsupported, f"not in brief: {', '.join(unsupported)}" if unsupported else "none found"),
    }
    return [
        {
            "criterion_id": c["criterion_id"],
            "label": c["label"],
            "passed": outcomes[c["criterion_id"]][0],
            "evidence": outcomes[c["criterion_id"]][1],
        }
        for c in rubric["criteria"]
    ]


def _submission_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = {
        k: row[k]
        for k in (
            "submission_id", "artifact_id", "rubric_id", "rubric_version", "status", "review_status",
            "appeal_reason", "created_at", "updated_at",
        )
    }
    data["results"] = loads(row["results_json"])
    return data


def submit(conn: sqlite3.Connection, registry: ContentRegistry, learner_id: str, artifact_id: str) -> dict[str, Any]:
    artifact = get_artifact(conn, learner_id, artifact_id)
    course = registry.course(artifact["course_id"])
    recipe = course.recipe(artifact["lesson_id"]) if course else None
    if recipe is None:
        raise ApiError(409, "no_rubric", "This lesson has no assessment rubric yet")
    rubric = course.rubrics[recipe["rubric_id"]]
    c = artifact["content"]
    fixture = course.fixtures[c["fixture_id"]]
    results = _criteria_results(
        rubric,
        checks.analyze_prompt(c["prompt"], fixture),
        checks.analyze_draft(c["draft_text"], fixture, rubric.get("max_words", 70)),
    )
    now = clock.now_iso()
    submission_id = new_id("sub")
    conn.execute(
        "INSERT INTO submissions (submission_id, artifact_id, learner_id, rubric_id, rubric_version, results_json,"
        " status, review_status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            submission_id, artifact_id, learner_id, rubric["rubric_id"], rubric["version"], dumps(results),
            "checks_passed" if all(r["passed"] for r in results) else "revision_requested",
            "not_reviewed", now, now,
        ),
    )
    return get_submission(conn, learner_id, submission_id)


def get_submission(conn: sqlite3.Connection, learner_id: str, submission_id: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM submissions WHERE submission_id = ? AND learner_id = ?", (submission_id, learner_id)
    ).fetchone()
    if row is None:
        raise not_found("Submission")
    return _submission_dict(row)


def list_submissions(conn: sqlite3.Connection, learner_id: str) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM submissions WHERE learner_id = ? ORDER BY created_at DESC", (learner_id,))
    return [_submission_dict(r) for r in rows]


def appeal(conn: sqlite3.Connection, learner_id: str, submission_id: str, reason: str) -> dict[str, Any]:
    get_submission(conn, learner_id, submission_id)
    conn.execute(
        "UPDATE submissions SET review_status = 'appeal_requested', appeal_reason = ?, updated_at = ?"
        " WHERE submission_id = ? AND learner_id = ?",
        (reason, clock.now_iso(), submission_id, learner_id),
    )
    return get_submission(conn, learner_id, submission_id)
