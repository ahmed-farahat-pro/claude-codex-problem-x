"""Learner memory (PRD section 12): short structured summaries the learner can view and delete.

Memory is learner scoped and separate from course retrieval. Deleting a memory removes the row, so it cannot
reach a later prompt or answer. Nothing is written when the learner has turned memory off.
"""

import sqlite3
from typing import Any

from . import clock
from .db import loads
from .ids import new_id
from .lab.content_studio import ContentStudio

KINDS = ("last_successful_task", "misconception", "next_practice")
ELEMENT_NAMES = {
    "task": ("المهمة", "task"),
    "context": ("السياق", "context"),
    "audience": ("الجمهور", "audience"),
    "constraints": ("القيود", "constraints"),
    "output_format": ("صيغة المخرجات", "output format"),
}


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in ("memory_id", "course_id", "kind", "text", "source_session_id", "updated_at")}


def list_memory(conn: sqlite3.Connection, learner_id: str, course_id: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM learning_memory WHERE learner_id = ?"
    params: list[Any] = [learner_id]
    if course_id:
        sql += " AND course_id = ?"
        params.append(course_id)
    return [_row_dict(r) for r in conn.execute(sql + " ORDER BY updated_at DESC", params)]


def delete_one(conn: sqlite3.Connection, learner_id: str, memory_id: str) -> bool:
    cur = conn.execute("DELETE FROM learning_memory WHERE memory_id = ? AND learner_id = ?", (memory_id, learner_id))
    return cur.rowcount > 0


def delete_all(conn: sqlite3.Connection, learner_id: str) -> int:
    return conn.execute("DELETE FROM learning_memory WHERE learner_id = ?", (learner_id,)).rowcount


def _upsert(conn: sqlite3.Connection, learner_id: str, course_id: str, kind: str, text: str, session_id: str) -> dict:
    conn.execute(
        "DELETE FROM learning_memory WHERE learner_id = ? AND course_id = ? AND kind = ?", (learner_id, course_id, kind)
    )
    item = {
        "memory_id": new_id("mem"),
        "course_id": course_id,
        "kind": kind,
        "text": text,
        "source_session_id": session_id,
        "updated_at": clock.now_iso(),
    }
    conn.execute(
        "INSERT INTO learning_memory (memory_id, learner_id, course_id, kind, text, source_session_id, updated_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (item["memory_id"], learner_id, course_id, kind, text, session_id, item["updated_at"]),
    )
    return item


def write_session_summary(
    conn: sqlite3.Connection,
    learner: sqlite3.Row,
    session: sqlite3.Row,
    lab_state: dict[str, Any],
    studio: ContentStudio,
) -> list[dict[str, Any]]:
    """Call inside the session-end transaction. Only the learner's own drafts count as their progress."""
    if not learner["memory_enabled"]:
        return []
    en = learner["language"] == "en"
    drafts = [d for d in lab_state.get("drafts", []) if d.get("created_by") == "learner"]
    saved = conn.execute(
        "SELECT content_json FROM artifacts WHERE session_id = ? AND learner_id = ? ORDER BY created_at DESC LIMIT 1",
        (session["session_id"], learner["learner_id"]),
    ).fetchone()
    if not drafts and saved is None:
        return []

    items: dict[str, str] = {}
    name = lab_state.get("business_name", "")
    if saved is not None:
        content = loads(saved["content_json"])
        words = content["checks"]["draft_checks"]["word_count"]
        items["last_successful_task"] = (
            f"Saved a draft for “{name}” ({words} words) in lesson {session['lesson_id']}."
            if en
            else f"حفظ مسودة لـ «{name}» ({words} كلمة) في الدرس {session['lesson_id']}."
        )
    else:
        items["last_successful_task"] = (
            f"Generated {len(drafts)} draft(s) for “{name}” without saving one."
            if en
            else f"ولّد {len(drafts)} مسودة لـ «{name}» دون حفظ أي منها."
        )
    if drafts:
        checks = studio.checks_for(drafts[-1])
        missing = [k for k in ELEMENT_NAMES if not checks["prompt_checks"][k]]
        if checks["draft_checks"]["unsupported_claims"]:
            items["misconception"] = (
                "The last draft contained claims that are not in the brief; ask for the supplied facts only."
                if en
                else "آخر مسودة احتوت ادعاءات غير موجودة في الملخص؛ اطلب «الحقائق المقدَّمة فقط»."
            )
        elif missing:
            names = [ELEMENT_NAMES[k][1 if en else 0] for k in missing]
            items["misconception"] = (
                f"The last prompt did not include: {', '.join(names)}."
                if en
                else f"آخر برومبت لم يتضمن: {'، '.join(names)}."
            )
    next_practice = studio.recipe.get("next_practice", {}).get("en" if en else "ar")
    if next_practice:
        items["next_practice"] = next_practice

    return [
        _upsert(conn, learner["learner_id"], session["course_id"], kind, text, session["session_id"])
        for kind, text in items.items()
    ]
