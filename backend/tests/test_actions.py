"""FR03 lab launch and reset, FR04 bounded tools, FR06 observation and verification."""

from app.lab.content_studio import Prepared


def test_learner_must_take_control_before_editing(learner):
    sid = learner.start()["session_id"]
    r = learner.act(sid, "set_prompt", {"text": "اكتب منشورًا"})
    assert r["status"] == "rejected" and r["error_category"] == "control"
    assert learner.state(sid)["lab"]["prompt"] == ""
    # reading and saving never need control
    assert learner.act(sid, "read_lab_state")["status"] == "succeeded"


def test_action_contract_and_observed_state_version(learner):
    sid = learner.start()["session_id"]
    learner.take_control(sid)
    r = learner.act(sid, "set_audience", {"text": "طلاب الجامعة"})
    assert set(r) >= {"action_id", "status", "observed_state_version", "result", "screenshot_ref", "duration_ms",
                      "error_category"}
    assert r["status"] == "succeeded" and r["observed_state_version"] == 2
    assert r["result"]["observed"] == "طلاب الجامعة"
    assert learner.state(sid)["lab"]["state_version"] == 2


def test_bounded_tools_reject_unknown_and_invalid_calls(learner):
    sid = learner.start()["session_id"]
    learner.take_control(sid)
    assert learner.act(sid, "run_shell", {"cmd": "ls"})["error_category"] == "unknown_tool"
    assert learner.act(sid, "set_prompt", {"text": "x" * 2001})["error_category"] == "validation"
    assert learner.act(sid, "set_prompt", {"text": "ok", "learner_id": "lrn_x"})["error_category"] == "validation"
    assert learner.act(sid, "open_lab", {"fixture_id": "someone-elses-fixture"})["error_category"] == "not_allowed"
    assert learner.act(sid, "generate_draft")["error_category"] == "validation"  # empty prompt
    assert learner.act(sid, "read_output")["error_category"] == "no_draft"
    assert learner.state(sid)["lab"]["state_version"] == 1


def test_idempotent_save_does_not_duplicate_artifacts(learner):
    sid = learner.start()["session_id"]
    learner.take_control(sid)
    learner.act(sid, "set_prompt", {"text": "اكتب منشورًا قصيرًا لمقهى الركن"})
    learner.act(sid, "generate_draft")
    first = learner.act(sid, "save_draft", key="save-key-0001")
    again = learner.act(sid, "save_draft", key="save-key-0001")
    assert first["status"] == "succeeded" and again["replayed"] is True
    assert again["result"]["artifact_id"] == first["result"]["artifact_id"]
    # a new key for the same content is deduplicated by content hash
    third = learner.act(sid, "save_draft")
    assert third["result"]["deduplicated"] is True
    assert len(learner.get("/api/me/artifacts").json()) == 1


def test_reset_restores_fixture_and_keeps_saved_work(learner):
    sid = learner.start()["session_id"]
    learner.say(sid, "اعرض البرومبت المنظم")
    learner.say(sid, "احفظ المسودة")
    learner.take_control(sid)
    r = learner.act(sid, "reset_lab")
    assert r["status"] == "succeeded"
    lab = learner.state(sid)["lab"]
    assert lab["prompt"] == "" and lab["drafts"] == [] and lab["fixture_id"] == "cafe-launch"
    assert len(learner.get("/api/me/artifacts").json()) == 1


def test_practice_fixture_can_be_opened(learner):
    sid = learner.start()["session_id"]
    turn = learner.say(sid, "أريد ملخص جديد للتمرين")
    assert [a["status"] for a in turn["actions"]] == ["succeeded"]
    assert learner.state(sid)["lab"]["fixture_id"] == "bookstore-evening"


def test_stale_epoch_is_refused(learner):
    sid = learner.start()["session_id"]
    learner.take_control(sid)
    epoch = learner.state(sid)["epoch"]
    learner.post(f"/api/sessions/{sid}/stop")
    r = learner.post(f"/api/sessions/{sid}/actions",
                     {"tool": "set_tone", "args": {"text": "رسمي"}, "epoch": epoch, "idempotency_key": "stale-key-01"})
    assert r.status_code == 409 and r.json()["error"]["current_epoch"] == epoch + 1


def test_unverified_action_is_not_reported_as_success(learner, monkeypatch):
    """If the expected state is not observed after the write, the step fails and the tutor says so."""
    from app.lab import content_studio

    original = content_studio.ContentStudio.prepare

    def broken_prepare(self, tool, args, state, actor):
        prepared = original(self, tool, args, state, actor)
        if tool == "generate_draft":
            return Prepared(apply=prepared.apply, verify=lambda observed, result: False, generation=prepared.generation)
        return prepared

    monkeypatch.setattr(content_studio.ContentStudio, "prepare", broken_prepare)
    sid = learner.start()["session_id"]
    turn = learner.say(sid, "اعرض البرومبت المنظم")
    statuses = [(a["tool"], a["status"]) for a in turn["actions"]]
    assert statuses[-1] == ("generate_draft", "failed")
    assert turn["actions"][-1]["error_category"] == "verification_failed"
    assert "read_output" not in [a["tool"] for a in turn["actions"]]  # nothing runs after a failed step
    assert "✗" in turn["answer"] and "ولّدتُ" not in turn["answer"]


def test_tutor_will_not_act_while_learner_holds_control(learner):
    sid = learner.start()["session_id"]
    learner.take_control(sid)
    turn = learner.say(sid, "اعرض البرومبت المنظم")
    assert turn["actions"] == [] and turn["answer_kind"] == "refusal"
    learner.post(f"/api/sessions/{sid}/control", {"holder": "tutor"})
    assert len(learner.say(sid, "اعرض البرومبت المنظم")["actions"]) == 5
