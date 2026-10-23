"""Tutor session lifecycle, generation epochs and the action path (PRD sections 10, 11 and 21).

Every event carries session_id, turn_id, epoch and a per-session sequence number. Stop and control changes
advance the epoch with one UPDATE and never wait for the model. Writes re-check the epoch inside the same
transaction, and a delayed model result is checked again before it is committed.
"""

import sqlite3
from datetime import timedelta
from typing import Any

from . import artifacts, clock, memory
from .db import dumps, loads, tx
from .errors import ApiError, not_found
from .ids import new_id
from .lab.content_studio import ContentStudio, public_state
from .lab.tools import TOOLS, ToolError, validate_call
from .services import Services

STATES = ("warming", "listening", "thinking", "acting", "speaking", "interrupted", "recovering", "ending", "ended")


class SessionService:
    def __init__(self, conn: sqlite3.Connection, services: Services):
        self.conn = conn
        self.services = services
        self.settings = services.settings

    # ------------------------------------------------------------------ lookup

    def row(self, learner_id: str, session_id: str) -> sqlite3.Row:
        row = self.conn.execute(
            "SELECT * FROM sessions WHERE session_id = ? AND learner_id = ?", (session_id, learner_id)
        ).fetchone()
        if row is None:
            raise not_found("Session")
        return row

    def _reload(self, session_id: str) -> sqlite3.Row:
        return self.conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()

    def studio(self, session: sqlite3.Row) -> ContentStudio:
        course = self.services.registry.course(session["course_id"])
        return ContentStudio(course, course.recipe(session["lesson_id"]), self.services.generator)

    def lab(self, session_id: str) -> tuple[dict[str, Any], int, str]:
        row = self.conn.execute(
            "SELECT state_json, state_version, status FROM lab_instances WHERE session_id = ?", (session_id,)
        ).fetchone()
        return loads(row["state_json"]), row["state_version"], row["status"]

    def _expiry_reason(self, session: sqlite3.Row) -> str | None:
        now = clock.now()
        if now >= clock.parse_iso(session["expires_at"]):
            return "time_cap"
        idle = (now - clock.parse_iso(session["last_activity_at"])).total_seconds()
        if idle > self.settings.idle_timeout_seconds:
            return "idle"
        return None

    def active_row(self, learner_id: str, session_id: str) -> sqlite3.Row:
        session = self.row(learner_id, session_id)
        if session["state"] == "ended":
            raise ApiError(409, "session_ended", "This session has ended", end_reason=session["end_reason"])
        reason = self._expiry_reason(session)
        if reason:
            self._end(session, reason)
            raise ApiError(409, "session_ended", f"This session has ended ({reason})", end_reason=reason)
        return session

    @staticmethod
    def check_epoch(session: sqlite3.Row, epoch: int) -> None:
        if session["epoch"] != epoch:
            raise ApiError(409, "stale_epoch", "The session moved on; refresh state", current_epoch=session["epoch"])

    def current_epoch(self, session_id: str) -> int:
        return self.conn.execute("SELECT epoch FROM sessions WHERE session_id = ?", (session_id,)).fetchone()[0]

    # ------------------------------------------------------------------ events and bookkeeping

    def event(self, session_id: str, type_: str, payload: dict[str, Any], *, epoch: int, turn_id: str | None = None):
        with tx(self.conn):
            seq = self.conn.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM events WHERE session_id = ?", (session_id,)
            ).fetchone()[0]
            self.conn.execute(
                "INSERT INTO events (session_id, seq, turn_id, epoch, type, payload_json, created_at)"
                " VALUES (?,?,?,?,?,?,?)",
                (session_id, seq, turn_id, epoch, type_, dumps(payload), clock.now_iso()),
            )

    def events(self, learner_id: str, session_id: str, after: int = 0, limit: int = 200) -> list[dict[str, Any]]:
        self.row(learner_id, session_id)
        rows = self.conn.execute(
            "SELECT * FROM events WHERE session_id = ? AND seq > ? ORDER BY seq LIMIT ?", (session_id, after, limit)
        )
        return [
            {
                "seq": r["seq"], "session_id": r["session_id"], "turn_id": r["turn_id"], "epoch": r["epoch"],
                "type": r["type"], "payload": loads(r["payload_json"]), "created_at": r["created_at"],
            }
            for r in rows
        ]

    def set_state(self, session_id: str, state: str, *, only_epoch: int | None = None) -> None:
        sql = "UPDATE sessions SET state = ?, last_activity_at = ? WHERE session_id = ? AND state != 'ended'"
        params: list[Any] = [state, clock.now_iso(), session_id]
        if only_epoch is not None:
            sql += " AND epoch = ?"
            params.append(only_epoch)
        with tx(self.conn):
            self.conn.execute(sql, params)

    def add_usage(self, session_id: str, input_tokens: int, output_tokens: int) -> None:
        if input_tokens or output_tokens:
            with tx(self.conn):
                self.conn.execute(
                    "UPDATE sessions SET model_input_tokens = model_input_tokens + ?,"
                    " model_output_tokens = model_output_tokens + ? WHERE session_id = ?",
                    (input_tokens, output_tokens, session_id),
                )

    def over_budget(self, session_id: str) -> bool:
        row = self._reload(session_id)
        return row["model_input_tokens"] + row["model_output_tokens"] >= self.settings.max_session_model_tokens

    # ------------------------------------------------------------------ lifecycle

    def create(self, learner: sqlite3.Row, course_id: str, lesson_id: str) -> dict[str, Any]:
        course = self.services.registry.course(course_id)
        if course is None or course.lesson(lesson_id) is None:
            raise not_found("Lesson")
        recipe = course.recipe(lesson_id)
        if recipe is None:
            raise ApiError(409, "lesson_not_ready", "This lesson has no lab recipe yet")
        enrollment = self.conn.execute(
            "SELECT * FROM enrollments WHERE learner_id = ? AND course_id = ?", (learner["learner_id"], course_id)
        ).fetchone()
        now = clock.now()
        if (
            enrollment is None
            or enrollment["status"] != "active"
            or (enrollment["expires_at"] and clock.parse_iso(enrollment["expires_at"]) <= now)
        ):
            raise ApiError(403, "not_entitled", "No active enrollment for this course")
        remaining = enrollment["live_allowance_seconds"] - enrollment["live_used_seconds"]
        if remaining <= 0:
            raise ApiError(403, "allowance_exhausted", "No live tutor minutes remain")

        for other in self.conn.execute(
            "SELECT * FROM sessions WHERE learner_id = ? AND state != 'ended'", (learner["learner_id"],)
        ).fetchall():
            reason = self._expiry_reason(other)
            if reason:
                self._end(other, reason)
            else:
                # One live session per learner. The client can resume it or end it.
                raise ApiError(409, "session_active", "You already have an active session", session_id=other["session_id"])

        studio = ContentStudio(course, recipe, self.services.generator)
        lab_state = studio.initial_state()
        if not studio.health_check(lab_state):
            raise ApiError(503, "lab_unhealthy", "The lab failed its health check")
        session_id = new_id("ses")
        started = clock.now_iso()
        expires = (now + timedelta(seconds=min(self.settings.max_session_seconds, remaining))).isoformat(
            timespec="milliseconds"
        )
        with tx(self.conn):
            self.conn.execute(
                "INSERT INTO sessions (session_id, learner_id, course_id, course_version, lesson_id, mode, state,"
                " started_at, expires_at, last_activity_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    session_id, learner["learner_id"], course_id, course.version, lesson_id, self.settings.mode,
                    "warming", started, expires, started,
                ),
            )
            self.conn.execute(
                "INSERT INTO lab_instances (session_id, template_id, template_version, status, state_json,"
                " state_version, updated_at) VALUES (?,?,?,?,?,?,?)",
                (session_id, studio.template_id, studio.template_version, "ready", dumps(lab_state), 1, started),
            )
            self.event(session_id, "session.created", {"lesson_id": lesson_id, "mode": self.settings.mode}, epoch=0)
            self.event(session_id, "lab.ready", {"fixture_id": lab_state["fixture_id"], "state_version": 1}, epoch=0)
            self.conn.execute("UPDATE sessions SET state = 'listening' WHERE session_id = ?", (session_id,))
        return self.snapshot(self._reload(session_id))

    def snapshot(self, session: sqlite3.Row) -> dict[str, Any]:
        lab_state, version, status = self.lab(session["session_id"])
        remaining = 0
        if session["state"] != "ended":
            remaining = max(0, int((clock.parse_iso(session["expires_at"]) - clock.now()).total_seconds()))
        return {
            "session_id": session["session_id"],
            "course_id": session["course_id"],
            "course_version": session["course_version"],
            "lesson_id": session["lesson_id"],
            "mode": session["mode"],
            "state": session["state"],
            "epoch": session["epoch"],
            "control": session["control"],
            "started_at": session["started_at"],
            "expires_at": session["expires_at"],
            "ended_at": session["ended_at"],
            "end_reason": session["end_reason"],
            "remaining_seconds": remaining,
            "lab": {"status": status, "state_version": version, **public_state(lab_state)},
            "usage": {
                "turns": session["turns"],
                "actions": session["actions"],
                "model_input_tokens": session["model_input_tokens"],
                "model_output_tokens": session["model_output_tokens"],
                "duration_seconds": session["duration_seconds"],
            },
        }

    def state(self, learner_id: str, session_id: str) -> dict[str, Any]:
        session = self.row(learner_id, session_id)
        if session["state"] != "ended":
            reason = self._expiry_reason(session)
            if reason:
                self._end(session, reason)
                session = self._reload(session_id)
        return self.snapshot(session)

    def stop(self, learner_id: str, session_id: str) -> dict[str, Any]:
        """Advance the epoch immediately. Completed actions stay completed; the response says so."""
        session = self.active_row(learner_id, session_id)
        with tx(self.conn):
            self.conn.execute(
                "UPDATE sessions SET epoch = epoch + 1, state = 'listening', last_activity_at = ? WHERE session_id = ?",
                (clock.now_iso(), session_id),
            )
            epoch = self.current_epoch(session_id)
            self.event(session_id, "stop", {"previous_epoch": session["epoch"]}, epoch=epoch)
        _, version, _ = self.lab(session_id)
        return {"session_id": session_id, "epoch": epoch, "state": "listening", "lab_state_version": version}

    def set_control(self, learner_id: str, session_id: str, holder: str) -> dict[str, Any]:
        session = self.active_row(learner_id, session_id)
        bump = 1 if holder == "learner" else 0  # taking control also stops the tutor
        with tx(self.conn):
            self.conn.execute(
                "UPDATE sessions SET control = ?, epoch = epoch + ?, state = 'listening', last_activity_at = ?"
                " WHERE session_id = ?",
                (holder, bump, clock.now_iso(), session_id),
            )
            epoch = self.current_epoch(session_id)
            self.event(session_id, "control", {"holder": holder, "previous": session["control"]}, epoch=epoch)
        return self.snapshot(self._reload(session_id))

    def end(self, learner_id: str, session_id: str) -> dict[str, Any]:
        session = self.row(learner_id, session_id)
        if session["state"] == "ended":
            return self._end_summary(session, [])
        return self._end(session, self._expiry_reason(session) or "learner_end")

    def _end(self, session: sqlite3.Row, reason: str) -> dict[str, Any]:
        session_id = session["session_id"]
        now = clock.now()
        stop_at = min(now, clock.parse_iso(session["expires_at"]))
        if reason == "idle":
            stop_at = min(stop_at, clock.parse_iso(session["last_activity_at"]))
        duration = max(0, int((stop_at - clock.parse_iso(session["started_at"])).total_seconds()))
        learner = self.conn.execute("SELECT * FROM learners WHERE learner_id = ?", (session["learner_id"],)).fetchone()
        studio = self.studio(session)
        written: list[dict[str, Any]] = []
        with tx(self.conn):
            current = self._reload(session_id)
            if current["state"] == "ended":  # a concurrent request ended it first
                return self._end_summary(current, [])
            lab_state, _, _ = self.lab(session_id)
            written = memory.write_session_summary(self.conn, learner, current, lab_state, studio)
            self.conn.execute(
                "UPDATE sessions SET state = 'ended', epoch = epoch + 1, ended_at = ?, end_reason = ?,"
                " duration_seconds = ? WHERE session_id = ?",
                (now.isoformat(timespec="milliseconds"), reason, duration, session_id),
            )
            self.conn.execute(
                "UPDATE enrollments SET live_used_seconds = live_used_seconds + ? WHERE learner_id = ? AND course_id = ?",
                (duration, session["learner_id"], session["course_id"]),
            )
            # Dispose the lab: drafts are dropped, saved artifacts live in learner storage.
            disposed = {"fixture_id": lab_state.get("fixture_id"), "disposed_at": now.isoformat(timespec="milliseconds")}
            self.conn.execute(
                "UPDATE lab_instances SET status = 'disposed', state_json = ?, updated_at = ? WHERE session_id = ?",
                (dumps(disposed), now.isoformat(timespec="milliseconds"), session_id),
            )
            self.event(
                session_id, "session.ended",
                {"reason": reason, "duration_seconds": duration, "memory_written": len(written)},
                epoch=current["epoch"] + 1,
            )
        return self._end_summary(self._reload(session_id), written)

    def _end_summary(self, session: sqlite3.Row, written: list[dict[str, Any]]) -> dict[str, Any]:
        enrollment = self.conn.execute(
            "SELECT live_allowance_seconds - live_used_seconds AS remaining FROM enrollments"
            " WHERE learner_id = ? AND course_id = ?",
            (session["learner_id"], session["course_id"]),
        ).fetchone()
        return {
            "session_id": session["session_id"],
            "state": session["state"],
            "end_reason": session["end_reason"],
            "usage": {
                "duration_seconds": session["duration_seconds"],
                "turns": session["turns"],
                "actions": session["actions"],
                "model_input_tokens": session["model_input_tokens"],
                "model_output_tokens": session["model_output_tokens"],
                "allowance_remaining_seconds": enrollment["remaining"] if enrollment else 0,
            },
            "memory_written": written,
        }

    # ------------------------------------------------------------------ actions

    def run_action(
        self,
        session: sqlite3.Row,
        *,
        actor: str,
        tool: str,
        args: dict[str, Any] | None,
        epoch: int,
        idempotency_key: str,
        turn_id: str | None = None,
    ) -> dict[str, Any]:
        """Validate, execute, observe and record one tool action. Returns the action contract."""
        started = clock.monotonic_ms()
        session_id = session["session_id"]
        action_id = new_id("act")
        try:
            with tx(self.conn):
                self.conn.execute(
                    "INSERT INTO actions (action_id, session_id, turn_id, epoch, actor, tool, args_json,"
                    " idempotency_key, status, result_json, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        action_id, session_id, turn_id, epoch, actor, tool, dumps(args or {}), idempotency_key,
                        "pending", "{}", clock.now_iso(),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            # Same idempotency key: return the recorded outcome instead of acting twice.
            prior = self.conn.execute(
                "SELECT status, result_json FROM actions WHERE session_id = ? AND idempotency_key = ?",
                (session_id, idempotency_key),
            ).fetchone()
            if prior["status"] == "pending":
                raise ApiError(409, "action_in_progress", "An action with this idempotency key is still running") from exc
            return {**loads(prior["result_json"]), "replayed": True}

        outcome: dict[str, Any] = {
            "action_id": action_id,
            "tool": tool,
            "actor": actor,
            "status": "failed",
            "observed_state_version": None,
            "result": None,
            "screenshot_ref": None,  # the server-state lab has no screen; the browser lab will fill this
            "duration_ms": 0,
            "error_category": None,
            "error_message": None,
            "replayed": False,
        }

        def finish(status: str, *, result=None, category=None, message=None, before=None, after=None):
            outcome.update(
                status=status, result=result, error_category=category, error_message=message,
                observed_state_version=after if after is not None else before,
                duration_ms=clock.monotonic_ms() - started,
            )
            with tx(self.conn):
                self.conn.execute(
                    "UPDATE actions SET status = ?, before_version = ?, after_version = ?, result_json = ?"
                    " WHERE action_id = ?",
                    (status, before, after, dumps(outcome), action_id),
                )
                self.conn.execute(
                    "UPDATE sessions SET actions = actions + 1, last_activity_at = ? WHERE session_id = ?",
                    (clock.now_iso(), session_id),
                )
                self.event(
                    session_id, "action",
                    {k: outcome[k] for k in ("action_id", "tool", "actor", "status", "observed_state_version",
                                             "error_category", "duration_ms")},
                    epoch=epoch, turn_id=turn_id,
                )
            return dict(outcome)

        current = self._reload(session_id)
        if current["state"] == "ended":
            return finish("rejected", category="session_ended", message="The session has ended")
        if current["epoch"] != epoch:
            return finish("stale", category="stale_epoch", message="Interrupted before this action ran")
        spec = TOOLS.get(tool)
        holds = current["control"]
        if actor == "tutor" and holds == "learner":
            return finish("rejected", category="control", message="The learner holds control of the lab")
        if actor == "learner" and holds == "tutor" and not (spec and spec.learner_without_control):
            return finish("rejected", category="control", message="Take control before editing the lab")

        studio = self.studio(current)
        lab_state, version, lab_status = self.lab(session_id)
        try:
            spec, parsed = validate_call(tool, args, studio.recipe["allowed_tools"])
            if lab_status != "ready":
                raise ToolError("lab_not_ready", "The lab is not ready")
            prepared = studio.prepare(tool, parsed, lab_state, actor)  # may call the model; no lock held
        except ToolError as exc:
            return finish("rejected" if exc.category in ("unknown_tool", "not_allowed", "validation") else "failed",
                          category=exc.category, message=exc.message, before=version)

        if prepared.generation:
            self.add_usage(session_id, prepared.generation.input_tokens, prepared.generation.output_tokens)
        if prepared.read_only:
            return finish("succeeded", result=prepared.result, before=version, after=version)

        saved: dict[str, Any] | None = None
        with tx(self.conn):
            now_row = self._reload(session_id)
            if now_row["epoch"] != epoch or now_row["state"] == "ended":
                stale = True
            else:
                stale = False
                latest, latest_version, _ = self.lab(session_id)
                if prepared.save is not None:
                    saved, deduplicated = artifacts.save_lab_draft(
                        self.conn, session["learner_id"], now_row, studio,
                        prepared.save["draft"], prepared.save["title"], prepared.save["note"],
                    )
                    result = {"artifact_id": saved["artifact_id"], "content_hash": saved["content_hash"],
                              "title": saved["title"], "deduplicated": deduplicated}
                    new_version = latest_version
                else:
                    new_state, result = prepared.apply(latest)
                    new_version = latest_version + 1
                    self.conn.execute(
                        "UPDATE lab_instances SET state_json = ?, state_version = ?, updated_at = ? WHERE session_id = ?",
                        (dumps(new_state), new_version, clock.now_iso(), session_id),
                    )
        if stale:
            return finish("stale", category="stale_epoch", message="Interrupted; the result was discarded", before=version)

        # Observe after commit and verify the expected change before reporting success.
        observed, observed_version, _ = self.lab(session_id)
        if saved is not None:
            ok = artifacts.artifact_exists(self.conn, session["learner_id"], saved["artifact_id"], saved["content_hash"])
        else:
            ok = prepared.verify(observed, result)
        if not ok:
            return finish("failed", result=result, category="verification_failed",
                          message="The expected lab state was not observed", before=version, after=observed_version)
        return finish("succeeded", result=result, before=version, after=observed_version)
