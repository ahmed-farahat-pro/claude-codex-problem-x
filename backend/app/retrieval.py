"""Course retrieval over approved passages with SQLite FTS5 (PRD section 12, demo retrieval).

Learner memory is deliberately not searched here: course content and learner memory stay separate.
"""

import sqlite3
from dataclasses import dataclass, field
from typing import Any

from . import textnorm
from .db import tx

MAX_QUERY_TERMS = 12


@dataclass
class Hit:
    passage_id: str
    lesson_id: str
    section_id: str
    title: str
    text: str
    source_url: str
    version: str
    score: float

    def source(self) -> dict[str, Any]:
        return {
            "passage_id": self.passage_id,
            "lesson_id": self.lesson_id,
            "section_id": self.section_id,
            "title": self.title,
            "source_url": self.source_url,
            "version": self.version,
        }


@dataclass
class RetrievalResult:
    terms: list[str]
    known_terms: list[str]
    hits: list[Hit] = field(default_factory=list)

    @property
    def is_vague(self) -> bool:
        return all(t in textnorm.VAGUE for t in self.terms)

    @property
    def in_scope(self) -> bool:
        """More than half of the question's content terms appear somewhere in the course."""
        return bool(self.hits) and len(self.known_terms) * 2 > len(self.terms)


def index_passages(conn: sqlite3.Connection, passages: list[dict[str, Any]]) -> None:
    with tx(conn):
        conn.execute("DELETE FROM passages")
        conn.execute("DELETE FROM passages_fts")
        for p in passages:
            conn.execute(
                "INSERT INTO passages (passage_id, course_id, lesson_id, section_id, version, language, title, text,"
                " source_url, reviewed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    p["passage_id"], p["course_id"], p["lesson_id"], p["section_id"], p["version"],
                    p["language"], p["title"], p["text"], p["source_url"], p["reviewed_at"],
                ),
            )
            conn.execute(
                "INSERT INTO passages_fts (passage_id, course_id, title_norm, text_norm) VALUES (?,?,?,?)",
                (
                    p["passage_id"], p["course_id"],
                    " ".join(textnorm.tokens(p["title"])),
                    " ".join(textnorm.tokens(p["text"])),
                ),
            )


def _fts_term(term: str) -> str:
    return '"' + term.replace('"', "") + '"*'


def _is_known(conn: sqlite3.Connection, course_id: str, term: str) -> bool:
    found = conn.execute(
        "SELECT 1 FROM passages_fts WHERE passages_fts MATCH ? AND course_id = ? LIMIT 1",
        (_fts_term(term), course_id),
    ).fetchone()
    return found is not None


def search(conn: sqlite3.Connection, course_id: str, question: str, limit: int = 3) -> RetrievalResult:
    terms = textnorm.content_tokens(question)[:MAX_QUERY_TERMS]
    result = RetrievalResult(terms=terms, known_terms=[])
    if not terms:
        return result
    for term in terms:
        if _is_known(conn, course_id, term):
            result.known_terms.append(term)
            continue
        # Learners ask with first-person verbs ("أحدد") while lessons use imperatives ("حدّد").
        if len(term) >= 4 and term[0] in "اينت" and _is_known(conn, course_id, term[1:]):
            result.known_terms.append(term[1:])
    if not result.known_terms:
        return result
    query = " OR ".join(_fts_term(t) for t in result.known_terms)
    rows = conn.execute(
        "SELECT p.*, bm25(passages_fts, 0.0, 0.0, 3.0, 1.0) AS score"
        " FROM passages_fts JOIN passages p ON p.passage_id = passages_fts.passage_id"
        " WHERE passages_fts MATCH ? AND passages_fts.course_id = ?"
        " ORDER BY score LIMIT ?",
        (query, course_id, limit),
    ).fetchall()
    result.hits = [
        Hit(
            passage_id=r["passage_id"], lesson_id=r["lesson_id"], section_id=r["section_id"], title=r["title"],
            text=r["text"], source_url=r["source_url"], version=r["version"], score=r["score"],
        )
        for r in rows
    ]
    return result
