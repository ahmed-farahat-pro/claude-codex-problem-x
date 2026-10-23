import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

COURSE = "ai-for-everyone"
LESSON = "L03"


class Learner:
    def __init__(self, client: TestClient, name: str = "Learner", language: str = "ar"):
        self.client = client
        body = client.post("/api/dev/learners", json={"display_name": name, "language": language}).json()
        self.learner_id = body["learner_id"]
        self.headers = {"Authorization": f"Bearer {body['token']}"}

    def get(self, path: str, **kw: Any):
        return self.client.get(path, headers=self.headers, **kw)

    def post(self, path: str, json: Any = None, **kw: Any):
        return self.client.post(path, json=json, headers=self.headers, **kw)

    def patch(self, path: str, json: Any = None):
        return self.client.patch(path, json=json, headers=self.headers)

    def delete(self, path: str):
        return self.client.delete(path, headers=self.headers)

    # -- session helpers

    def start(self, lesson: str = LESSON) -> dict[str, Any]:
        r = self.post("/api/sessions", {"course_id": COURSE, "lesson_id": lesson})
        assert r.status_code == 201, r.text
        return r.json()

    def state(self, sid: str) -> dict[str, Any]:
        r = self.get(f"/api/sessions/{sid}/state")
        assert r.status_code == 200, r.text
        return r.json()

    def say(self, sid: str, text: str) -> dict[str, Any]:
        r = self.post(f"/api/sessions/{sid}/messages", {"text": text, "epoch": self.state(sid)["epoch"]})
        assert r.status_code == 200, r.text
        return r.json()

    def act(self, sid: str, tool: str, args: dict | None = None, key: str | None = None) -> dict[str, Any]:
        body = {"tool": tool, "args": args or {}, "epoch": self.state(sid)["epoch"],
                "idempotency_key": key or uuid.uuid4().hex}
        r = self.post(f"/api/sessions/{sid}/actions", body)
        assert r.status_code == 200, r.text
        return r.json()

    def take_control(self, sid: str) -> dict[str, Any]:
        return self.post(f"/api/sessions/{sid}/control", {"holder": "learner"}).json()


@pytest.fixture
def make_app(tmp_path: Path) -> Callable[..., TestClient]:
    def factory(**kwargs: Any) -> TestClient:
        overrides = {k: kwargs.pop(k) for k in list(kwargs) if k in Settings.model_fields}
        settings = Settings(_env_file=None, mode="deterministic", db_path=tmp_path / "test.db", **overrides)
        return TestClient(create_app(settings, **kwargs))

    return factory


@pytest.fixture
def client(make_app) -> TestClient:
    return make_app()


@pytest.fixture
def learner(client) -> Learner:
    return Learner(client, "Sara")


@pytest.fixture
def other(client) -> Learner:
    return Learner(client, "Omar")


@pytest.fixture
def new_learner() -> Callable[..., Learner]:
    return Learner
