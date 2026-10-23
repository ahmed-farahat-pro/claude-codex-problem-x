"""PRD section 23 'Isolation': no learner A data is returned to learner B."""


def _a_with_everything(learner):
    sid = learner.start()["session_id"]
    learner.say(sid, "اعرض البرومبت المنظم")
    saved = learner.say(sid, "احفظ المسودة")["actions"][0]["result"]
    artifact_id = saved["artifact_id"]
    submission_id = learner.post(f"/api/me/artifacts/{artifact_id}/submissions").json()["submission_id"]
    learner.take_control(sid)
    learner.act(sid, "set_prompt", {"text": "اكتب منشورًا لمقهى الركن"})
    learner.act(sid, "generate_draft")
    learner.post(f"/api/sessions/{sid}/end")
    memory_id = learner.get("/api/me/memory").json()[0]["memory_id"]
    return sid, artifact_id, submission_id, memory_id


def test_learner_b_cannot_reach_learner_a_data(learner, other):
    sid, artifact_id, submission_id, memory_id = _a_with_everything(learner)
    attempts = [
        other.get(f"/api/sessions/{sid}/state"),
        other.get(f"/api/sessions/{sid}/events"),
        other.get(f"/api/sessions/{sid}/turns"),
        other.post(f"/api/sessions/{sid}/messages", {"text": "hi", "epoch": 0}),
        other.post(f"/api/sessions/{sid}/actions",
                   {"tool": "read_lab_state", "args": {}, "epoch": 0, "idempotency_key": "cross-account-1"}),
        other.post(f"/api/sessions/{sid}/stop"),
        other.post(f"/api/sessions/{sid}/end"),
        other.post(f"/api/sessions/{sid}/control", {"holder": "learner"}),
        other.get(f"/api/me/artifacts/{artifact_id}"),
        other.get(f"/api/me/artifacts/{artifact_id}/export"),
        other.post(f"/api/me/artifacts/{artifact_id}/submissions"),
        other.get(f"/api/me/submissions/{submission_id}"),
        other.post(f"/api/me/submissions/{submission_id}/appeal", {"reason": "please"}),
        other.delete(f"/api/me/memory/{memory_id}"),
    ]
    for r in attempts:
        assert r.status_code == 404, (r.request.url, r.status_code, r.text)
    assert other.get("/api/me/artifacts").json() == []
    assert other.get("/api/me/memory").json() == []
    assert other.get("/api/me/submissions").json() == []
    # and A's data is untouched
    assert learner.get(f"/api/me/artifacts/{artifact_id}").status_code == 200
    assert len(learner.get("/api/me/memory").json()) >= 1


def test_reset_memory_only_touches_own_rows(learner, other):
    _a_with_everything(learner)
    other.delete("/api/me/memory")
    assert len(learner.get("/api/me/memory").json()) >= 1
