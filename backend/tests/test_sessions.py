from datetime import timedelta

from app import clock
from app.llm.base import ModelStep


def test_create_session_provisions_a_healthy_lab(learner):
    s = learner.start()
    assert s["state"] == "listening" and s["control"] == "tutor" and s["epoch"] == 0
    assert s["mode"] == "deterministic"
    assert s["lab"]["status"] == "ready" and s["lab"]["fixture_id"] == "cafe-launch"
    assert s["lab"]["brief"] and s["lab"]["drafts"] == []
    assert 0 < s["remaining_seconds"] <= 600
    types = [e["type"] for e in learner.get(f"/api/sessions/{s['session_id']}/events").json()]
    assert types[:2] == ["session.created", "lab.ready"]


def test_lesson_without_recipe_is_not_ready(learner):
    r = learner.post("/api/sessions", {"course_id": "ai-for-everyone", "lesson_id": "L01"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "lesson_not_ready"


def test_one_active_session_per_learner(learner):
    first = learner.start()["session_id"]
    r = learner.post("/api/sessions", {"course_id": "ai-for-everyone", "lesson_id": "L03"})
    assert r.status_code == 409
    assert r.json()["error"] == {
        "code": "session_active", "message": "You already have an active session", "session_id": first
    }


def test_requires_authentication(client):
    assert client.post("/api/sessions", json={"course_id": "ai-for-everyone", "lesson_id": "L03"}).status_code == 401
    assert client.get("/api/me", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_dev_login_can_be_disabled(make_app):
    client = make_app(dev_auth=False)
    assert client.post("/api/dev/learners", json={}).status_code == 404


def test_end_settles_usage_and_disposes_lab(learner):
    sid = learner.start()["session_id"]
    learner.say(sid, "اعرض البرومبت المنظم")
    end = learner.post(f"/api/sessions/{sid}/end").json()
    assert end["state"] == "ended" and end["end_reason"] == "learner_end"
    assert end["usage"]["turns"] == 1 and end["usage"]["actions"] == 5
    state = learner.state(sid)
    assert state["lab"]["status"] == "disposed" and state["lab"]["drafts"] == []
    r = learner.post(f"/api/sessions/{sid}/messages", {"text": "مرحبا", "epoch": state["epoch"]})
    assert r.status_code == 409 and r.json()["error"]["code"] == "session_ended"
    # ending twice is harmless and does not bill twice
    used = learner.get("/api/me/enrollments").json()[0]["live_used_seconds"]
    learner.post(f"/api/sessions/{sid}/end")
    assert learner.get("/api/me/enrollments").json()[0]["live_used_seconds"] == used


def test_time_cap_ends_session(learner, monkeypatch):
    sid = learner.start()["session_id"]
    later = clock.now() + timedelta(seconds=601)
    monkeypatch.setattr(clock, "now", lambda: later)
    state = learner.state(sid)
    assert state["state"] == "ended" and state["end_reason"] == "time_cap"
    assert learner.get("/api/me/enrollments").json()[0]["live_used_seconds"] == 600


def test_idle_session_expires_and_bills_only_active_time(learner, monkeypatch):
    sid = learner.start()["session_id"]
    later = clock.now() + timedelta(seconds=301)
    monkeypatch.setattr(clock, "now", lambda: later)
    r = learner.post(f"/api/sessions/{sid}/stop")
    assert r.status_code == 409 and r.json()["error"]["end_reason"] == "idle"
    assert learner.get("/api/me/enrollments").json()[0]["live_used_seconds"] <= 1
    # an expired session no longer blocks a new one
    assert learner.start()["session_id"] != sid


def test_allowance_exhausted(make_app, new_learner):
    learner = new_learner(make_app(dev_live_allowance_seconds=0))
    r = learner.post("/api/sessions", {"course_id": "ai-for-everyone", "lesson_id": "L03"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "allowance_exhausted"


def test_session_length_is_capped_by_remaining_allowance(make_app, new_learner):
    learner = new_learner(make_app(dev_live_allowance_seconds=120))
    assert learner.start()["remaining_seconds"] <= 120


def test_token_budget_stops_the_turn_honestly(make_app, new_learner):
    class Expensive:
        def start(self, ctx):
            return self

        def step(self, results):
            return ModelStep(text="ok", input_tokens=900, output_tokens=200)

    learner = new_learner(make_app(max_session_model_tokens=1000, tutor=Expensive()))
    sid = learner.start()["session_id"]
    assert learner.say(sid, "سؤال")["status"] == "completed"
    turn = learner.say(sid, "سؤال آخر")
    assert turn["status"] == "failed" and turn["error_category"] == "budget_exceeded"
    assert turn["answer_kind"] == "error" and turn["answer"]
