-- SQLite schema for the local starter. Times are UTC ISO-8601 strings; durations are integers.

CREATE TABLE IF NOT EXISTS learners (
    learner_id        TEXT PRIMARY KEY,
    display_name      TEXT NOT NULL,
    language          TEXT NOT NULL DEFAULT 'ar',
    explanation_pref  TEXT NOT NULL DEFAULT 'detailed',
    memory_enabled    INTEGER NOT NULL DEFAULT 1,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS api_tokens (
    token_hash  TEXT PRIMARY KEY,
    learner_id  TEXT NOT NULL REFERENCES learners(learner_id),
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS enrollments (
    learner_id              TEXT NOT NULL REFERENCES learners(learner_id),
    course_id               TEXT NOT NULL,
    status                  TEXT NOT NULL,
    expires_at              TEXT,
    live_allowance_seconds  INTEGER NOT NULL DEFAULT 0,
    live_used_seconds       INTEGER NOT NULL DEFAULT 0,
    organisation_id         TEXT,
    created_at              TEXT NOT NULL,
    PRIMARY KEY (learner_id, course_id)
);

CREATE TABLE IF NOT EXISTS progress (
    learner_id      TEXT NOT NULL REFERENCES learners(learner_id),
    course_id       TEXT NOT NULL,
    lesson_id       TEXT NOT NULL,
    lesson_version  TEXT NOT NULL,
    status          TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    PRIMARY KEY (learner_id, course_id, lesson_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id           TEXT PRIMARY KEY,
    learner_id           TEXT NOT NULL REFERENCES learners(learner_id),
    course_id            TEXT NOT NULL,
    course_version       TEXT NOT NULL,
    lesson_id            TEXT NOT NULL,
    mode                 TEXT NOT NULL,
    state                TEXT NOT NULL,
    epoch                INTEGER NOT NULL DEFAULT 0,
    control              TEXT NOT NULL DEFAULT 'tutor',
    started_at           TEXT NOT NULL,
    expires_at           TEXT NOT NULL,
    last_activity_at     TEXT NOT NULL,
    ended_at             TEXT,
    end_reason           TEXT,
    turns                INTEGER NOT NULL DEFAULT 0,
    actions              INTEGER NOT NULL DEFAULT 0,
    model_input_tokens   INTEGER NOT NULL DEFAULT 0,
    model_output_tokens  INTEGER NOT NULL DEFAULT 0,
    duration_seconds     INTEGER
);
CREATE INDEX IF NOT EXISTS sessions_by_learner ON sessions(learner_id, started_at);

CREATE TABLE IF NOT EXISTS lab_instances (
    session_id        TEXT PRIMARY KEY REFERENCES sessions(session_id),
    template_id       TEXT NOT NULL,
    template_version  TEXT NOT NULL,
    status            TEXT NOT NULL,
    state_json        TEXT NOT NULL,
    state_version     INTEGER NOT NULL,
    updated_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS turns (
    turn_id       TEXT PRIMARY KEY,
    session_id    TEXT NOT NULL REFERENCES sessions(session_id),
    epoch         INTEGER NOT NULL,
    status        TEXT NOT NULL,
    user_text     TEXT NOT NULL,
    answer_text   TEXT,
    answer_kind   TEXT,
    sources_json  TEXT NOT NULL DEFAULT '[]',
    created_at    TEXT NOT NULL,
    completed_at  TEXT
);
CREATE INDEX IF NOT EXISTS turns_by_session ON turns(session_id, created_at);

CREATE TABLE IF NOT EXISTS actions (
    action_id        TEXT PRIMARY KEY,
    session_id       TEXT NOT NULL REFERENCES sessions(session_id),
    turn_id          TEXT,
    epoch            INTEGER NOT NULL,
    actor            TEXT NOT NULL,
    tool             TEXT NOT NULL,
    args_json        TEXT NOT NULL,
    idempotency_key  TEXT NOT NULL,
    status           TEXT NOT NULL,
    before_version   INTEGER,
    after_version    INTEGER,
    result_json      TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    UNIQUE (session_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS events (
    session_id    TEXT NOT NULL REFERENCES sessions(session_id),
    seq           INTEGER NOT NULL,
    turn_id       TEXT,
    epoch         INTEGER NOT NULL,
    type          TEXT NOT NULL,
    payload_json  TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    PRIMARY KEY (session_id, seq)
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id   TEXT PRIMARY KEY,
    learner_id    TEXT NOT NULL REFERENCES learners(learner_id),
    session_id    TEXT,
    course_id     TEXT NOT NULL,
    lesson_id     TEXT NOT NULL,
    kind          TEXT NOT NULL,
    title         TEXT NOT NULL,
    content_json  TEXT NOT NULL,
    content_hash  TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS artifacts_by_learner ON artifacts(learner_id, created_at);

CREATE TABLE IF NOT EXISTS submissions (
    submission_id   TEXT PRIMARY KEY,
    artifact_id     TEXT NOT NULL REFERENCES artifacts(artifact_id),
    learner_id      TEXT NOT NULL REFERENCES learners(learner_id),
    rubric_id       TEXT NOT NULL,
    rubric_version  TEXT NOT NULL,
    results_json    TEXT NOT NULL,
    status          TEXT NOT NULL,
    review_status   TEXT NOT NULL,
    appeal_reason   TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS learning_memory (
    memory_id          TEXT PRIMARY KEY,
    learner_id         TEXT NOT NULL REFERENCES learners(learner_id),
    course_id          TEXT NOT NULL,
    kind               TEXT NOT NULL,
    text               TEXT NOT NULL,
    source_session_id  TEXT,
    updated_at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS memory_by_learner ON learning_memory(learner_id);

-- Approved course content. Rebuilt from content/ on startup.
CREATE TABLE IF NOT EXISTS passages (
    passage_id   TEXT PRIMARY KEY,
    course_id    TEXT NOT NULL,
    lesson_id    TEXT NOT NULL,
    section_id   TEXT NOT NULL,
    version      TEXT NOT NULL,
    language     TEXT NOT NULL,
    title        TEXT NOT NULL,
    text         TEXT NOT NULL,
    source_url   TEXT NOT NULL,
    reviewed_at  TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS passages_fts USING fts5(
    passage_id UNINDEXED,
    course_id UNINDEXED,
    title_norm,
    text_norm,
    tokenize = 'unicode61'
);
