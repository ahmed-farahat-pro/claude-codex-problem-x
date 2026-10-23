"""Stop and interruption (PRD section 11): advance the epoch, discard late work, never undo completed actions."""

from app import db
from app.llm.base import ModelStep, ToolCall
from app.sessions import SessionService


class StopsMidTurn:
    """A fake model that presses Stop (from another connection) at a chosen point in the turn."""

    def __init__(self, app_services, learner_id, when: str):
        self.services = app_services
        self.learner_id = learner_id
        self.when = when
        self.session_id = None

    def press_stop(self):
        conn = db.connect(self.services.settings.db_path)
        try:
            SessionService(conn, self.services).stop(self.learner_id, self.session_id)
        finally:
            conn.close()

    def start(self, ctx):
        self.calls = 0
        return self

    def step(self, results):
        self.calls += 1
        if self.when == "before_answer":
            self.press_stop()  # the model result arrives after Stop and must be discarded
            return ModelStep(text="late answer")
        if self.calls == 1:
            return ModelStep(tool_calls=[
                ToolCall("set_prompt", {"text": "اكتب منشورًا قصيرًا لمقهى الركن"}),
                ToolCall("generate_draft", {}),
            ])
        return ModelStep(text="explained")


def _setup(make_app, new_learner, when):
    holder = {}

    class Proxy:
        def start(self, ctx):
            return holder["model"].start(ctx)

    client = make_app(tutor=Proxy())
    learner = new_learner(client)
    model = StopsMidTurn(client.app.state.services, learner.learner_id, when)
    holder["model"] = model
    sid = learner.start()["session_id"]
    model.session_id = sid
    return learner, model, sid


def test_late_model_result_is_discarded(make_app, new_learner):
    learner, _, sid = _setup(make_app, new_learner, "before_answer")
    turn = learner.say(sid, "سؤال")
    assert turn["status"] == "interrupted" and turn["answer"] is None
    assert turn["current_epoch"] == 1
    events = [e["type"] for e in learner.get(f"/api/sessions/{sid}/events").json()]
    assert "turn.interrupted" in events and "answer" not in events


def test_stop_between_tools_prevents_the_next_write(make_app, new_learner, monkeypatch):
    learner, model, sid = _setup(make_app, new_learner, "between_tools")
    original = SessionService.run_action

    def run_then_stop(self, session, **kw):
        outcome = original(self, session, **kw)
        if kw["tool"] == "set_prompt":
            model.press_stop()
        return outcome

    monkeypatch.setattr(SessionService, "run_action", run_then_stop)
    turn = learner.say(sid, "اعرض")
    assert turn["status"] == "interrupted"
    assert [(a["tool"], a["status"]) for a in turn["actions"]] == [
        ("set_prompt", "succeeded"),
        ("generate_draft", "stale"),
    ]
    lab = learner.state(sid)["lab"]
    # The completed action stays completed; the stale one never wrote anything.
    assert lab["prompt"] == "اكتب منشورًا قصيرًا لمقهى الركن"
    assert lab["drafts"] == []


def test_stop_endpoint_advances_epoch_and_reports_lab_version(learner):
    sid = learner.start()["session_id"]
    learner.say(sid, "اعرض البرومبت المنظم")
    r = learner.post(f"/api/sessions/{sid}/stop").json()
    assert r["epoch"] == 1 and r["state"] == "listening" and r["lab_state_version"] == 5
    # Stop does not undo completed work: the draft is still there.
    assert len(learner.state(sid)["lab"]["drafts"]) == 1


def test_taking_control_interrupts_the_tutor(learner):
    sid = learner.start()["session_id"]
    before = learner.state(sid)["epoch"]
    after = learner.take_control(sid)
    assert after["control"] == "learner" and after["epoch"] == before + 1


def test_unexpected_model_error_fails_the_turn_honestly(make_app, new_learner):
    class Broken:
        def start(self, ctx):
            raise KeyError("bug")

    learner = new_learner(make_app(tutor=Broken()))
    sid = learner.start()["session_id"]
    turn = learner.say(sid, "سؤال")
    assert turn["status"] == "failed" and turn["error_category"] == "internal_error"
    assert learner.state(sid)["state"] == "listening"
    assert learner.get(f"/api/sessions/{sid}/turns").json()[0]["status"] == "failed"
