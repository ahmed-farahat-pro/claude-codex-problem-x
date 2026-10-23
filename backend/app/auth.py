"""Learner identity.

The learner id always comes from the server-side token lookup. Request bodies and model output never choose
whose data is read or written. Production authentication is a later build phase; the dev login below exists
only for local work and is disabled with FOURWEEKS_DEV_AUTH=false.
"""

import hashlib
import secrets
import sqlite3

from fastapi import Request

from . import clock
from .config import Settings
from .content import ContentRegistry
from .db import tx
from .errors import ApiError
from .ids import new_id


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_dev_learner(
    conn: sqlite3.Connection, settings: Settings, registry: ContentRegistry, display_name: str, language: str
) -> tuple[str, str]:
    learner_id = new_id("lrn")
    token = secrets.token_urlsafe(32)
    now = clock.now_iso()
    with tx(conn):
        conn.execute(
            "INSERT INTO learners (learner_id, display_name, language, created_at) VALUES (?,?,?,?)",
            (learner_id, display_name, language, now),
        )
        conn.execute(
            "INSERT INTO api_tokens (token_hash, learner_id, created_at) VALUES (?,?,?)",
            (hash_token(token), learner_id, now),
        )
        for course_id in registry.courses:
            conn.execute(
                "INSERT INTO enrollments (learner_id, course_id, status, live_allowance_seconds, created_at)"
                " VALUES (?,?,?,?,?)",
                (learner_id, course_id, "active", settings.dev_live_allowance_seconds, now),
            )
    return learner_id, token


def learner_from_request(conn: sqlite3.Connection, request: Request) -> sqlite3.Row:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ApiError(401, "unauthenticated", "Missing bearer token")
    row = conn.execute(
        "SELECT l.* FROM api_tokens t JOIN learners l ON l.learner_id = t.learner_id WHERE t.token_hash = ?",
        (hash_token(token.strip()),),
    ).fetchone()
    if row is None:
        raise ApiError(401, "unauthenticated", "Invalid token")
    return row
