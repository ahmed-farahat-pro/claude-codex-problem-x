"""Tutor coordinator: one learner message becomes one cancellable, observable turn (PRD section 10).

retrieve -> model step -> validated tools -> observed results -> model explains -> commit answer.
The epoch is checked before every model step, after every model result and before the answer is committed,
so Stop discards late work without waiting for the model.
"""

import logging
import sqlite3
from typing import Any

from . import clock, memory, retrieval
from .db import dumps, loads, tx
from .ids import new_id
from .lab.content_studio import public_state
from .llm.base import ModelStep, ProviderError, TurnContext
from .sessions import SessionService

HISTORY_TURNS = 6
log = logging.getLogger(__name__)

FAILURE_TEXT = {
    "provider_error": (
        "تعذّر الحصول على إجابة من النموذج الآن. عملك في المختبر محفوظ، ويمكنك إعادة المحاولة.",
        "I could not get an answer from the model right now. Your lab work is kept; you can try again.",
    ),
    "budget_exceeded": (
        "وصلت هذه الجلسة إلى حد الاستخدام المسموح. احفظ عملك وأنهِ الجلسة، أو تابع بالأسئلة النصية لاحقًا.",
        "This session reached its usage limit. Save your work and end the session.",
    ),
    "internal_error": (
        "حدث خطأ غير متوقع في هذه الخطوة. عملك المحفوظ لم يتأثر؛ أعد المحاولة أو أعد ضبط المختبر.",
        "Something unexpected went wrong in this step. Your saved work is unaffected; try again or reset the lab.",
    ),
    "step_limit": (
        "توقفتُ لأن هذه الإجابة احتاجت خطوات أكثر من المسموح. جرّب طلبًا أصغر.",
        "I stopped because this answer needed more steps than allowed. Try a smaller request.",
    ),
}


class TutorCoordinator:
    def __init__(self, sessions: SessionService):
        self.sessions = sessions
        self.conn: sqlite3.Connection = sessions.conn
        self.services = sessions.services
        self.settings = sessions.settings

    def _history(self, session_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT user_text, answer_text FROM turns WHERE session_id = ? AND status = 'completed'"
            " ORDER BY created_at DESC LIMIT ?",
            (session_id, HISTORY_TURNS),
        ).fetchall()
        return [{"user": r["user_text"], "tutor": r["answer_text"]} for r in reversed(rows)]

    def handle_message(self, learner: sqlite3.Row, session_id: str, text: str, epoch: int) -> dict[str, Any]:
        sessions = self.sessions
        session = sessions.active_row(learner["learner_id"], session_id)
        sessions.check_epoch(session, epoch)
        turn_id = new_id("trn")
        with tx(self.conn):
            self.conn.execute(
                "INSERT INTO turns (turn_id, session_id, epoch, status, user_text, created_at) VALUES (?,?,?,?,?,?)",
                (turn_id, session_id, epoch, "running", text, clock.now_iso()),
            )
            self.conn.execute(
                "UPDATE sessions SET turns = turns + 1, state = 'thinking', last_activity_at = ? WHERE session_id = ?",
                (clock.now_iso(), session_id),
            )
            sessions.event(session_id, "turn.started", {"text": text}, epoch=epoch, turn_id=turn_id)

        studio = sessions.studio(session)
        found = retrieval.search(self.conn, session["course_id"], text)
        sessions.event(
            session_id, "retrieval",
            {"terms": found.terms, "passage_ids": [h.passage_id for h in found.hits], "in_scope": found.in_scope},
            epoch=epoch, turn_id=turn_id,
        )
        lab_state, _, _ = sessions.lab(session_id)
        ctx = TurnContext(
            user_text=text,
            language=learner["language"],
            explanation_pref=learner["explanation_pref"],
            display_name=learner["display_name"],
            memory=memory.list_memory(self.conn, learner["learner_id"], session["course_id"])
            if learner["memory_enabled"] else [],
            lesson=self.services.registry.course(session["course_id"]).lesson(session["lesson_id"]),
            recipe=studio.recipe,
            fixture=studio.fixture(lab_state["fixture_id"]),
            lab_state=public_state(lab_state),
            control=session["control"],
            retrieval=found,
            history=self._history(session_id),
            allowed_tools=studio.recipe["allowed_tools"],
        )

        actions: list[dict[str, Any]] = []
        try:
            status, error, final = self._run_loop(session, session_id, turn_id, epoch, ctx, actions)
        except Exception:
            log.exception("tutor turn %s failed", turn_id)
            status, error, final = "failed", "internal_error", None
        return self._commit(learner, session_id, turn_id, epoch, status, error, final, found, actions)

    def _run_loop(self, session, session_id, turn_id, epoch, ctx, actions) -> tuple[str, str | None, ModelStep | None]:
        sessions = self.sessions
        conversation = self.services.tutor.start(ctx)
        results: list[dict[str, Any]] = []
        final: ModelStep | None = None
        status, error = "completed", None
        calls_made, steps = 0, 0

        while True:
            if sessions.current_epoch(session_id) != epoch:
                status = "interrupted"
                break
            if sessions.over_budget(session_id):
                status, error = "failed", "budget_exceeded"
                break
            if steps > self.settings.max_tool_calls_per_turn:
                status, error = "failed", "step_limit"
                break
            steps += 1
            try:
                step = conversation.step(results)
            except ProviderError:
                status, error = "failed", "provider_error"
                break
            sessions.add_usage(session_id, step.input_tokens, step.output_tokens)
            if sessions.current_epoch(session_id) != epoch:  # a late model result is discarded
                status = "interrupted"
                break
            if not step.tool_calls:
                final = step
                break

            sessions.set_state(session_id, "acting", only_epoch=epoch)
            results = []
            blocked: str | None = None
            for call in step.tool_calls:
                if blocked or calls_made >= self.settings.max_tool_calls_per_turn:
                    # Every call gets a response, but nothing runs after a failure or past the limit.
                    results.append({"tool": call.name, "call_id": call.call_id, "status": "skipped",
                                    "error_category": blocked or "limit", "result": None})
                    continue
                calls_made += 1
                outcome = sessions.run_action(
                    session, actor="tutor", tool=call.name, args=call.args, epoch=epoch,
                    idempotency_key=f"{turn_id}:{calls_made}", turn_id=turn_id,
                )
                outcome["call_id"] = call.call_id
                results.append(outcome)
                actions.append(outcome)
                if outcome["status"] == "stale":
                    status = "interrupted"
                    break
                if outcome["status"] != "succeeded":
                    blocked = "previous_step_failed"
            if status == "interrupted":
                break
            sessions.set_state(session_id, "thinking", only_epoch=epoch)
        return status, error, final

    def _commit(self, learner, session_id, turn_id, epoch, status, error, final, found, actions) -> dict[str, Any]:
        sessions = self.sessions
        answer, kind, sources = None, None, []
        with tx(self.conn):
            if status == "completed" and sessions.current_epoch(session_id) != epoch:
                status = "interrupted"
            if status == "completed":
                by_id = {h.passage_id: h for h in found.hits}
                sources = [by_id[pid].source() for pid in dict.fromkeys(final.cited) if pid in by_id]
                answer, kind = final.text or "", final.kind
            elif status == "failed":
                ar, en = FAILURE_TEXT[error]
                answer, kind = (en if learner["language"] == "en" else ar), "error"
            self.conn.execute(
                "UPDATE turns SET status = ?, answer_text = ?, answer_kind = ?, sources_json = ?, completed_at = ?"
                " WHERE turn_id = ?",
                (status, answer, kind, dumps(sources), clock.now_iso(), turn_id),
            )
            if status == "interrupted":
                sessions.event(session_id, "turn.interrupted", {}, epoch=epoch, turn_id=turn_id)
            else:
                sessions.event(
                    session_id, "answer",
                    {"kind": kind, "text": answer, "sources": sources, "error_category": error},
                    epoch=epoch, turn_id=turn_id,
                )
                sessions.set_state(session_id, "listening", only_epoch=epoch)
        session = sessions._reload(session_id)
        _, version, _ = sessions.lab(session_id)
        return {
            "turn_id": turn_id,
            "epoch": epoch,
            "status": status,
            "answer": answer,
            "answer_kind": kind,
            "error_category": error,
            "sources": sources,
            "actions": actions,
            "state": session["state"],
            "current_epoch": session["epoch"],
            "lab_state_version": version,
        }

    def turns(self, learner_id: str, session_id: str) -> list[dict[str, Any]]:
        self.sessions.row(learner_id, session_id)
        rows = self.conn.execute(
            "SELECT * FROM turns WHERE session_id = ? ORDER BY created_at", (session_id,)
        ).fetchall()
        return [
            {
                "turn_id": r["turn_id"], "epoch": r["epoch"], "status": r["status"], "user_text": r["user_text"],
                "answer": r["answer_text"], "answer_kind": r["answer_kind"], "sources": loads(r["sources_json"]),
                "created_at": r["created_at"], "completed_at": r["completed_at"],
            }
            for r in rows
        ]
