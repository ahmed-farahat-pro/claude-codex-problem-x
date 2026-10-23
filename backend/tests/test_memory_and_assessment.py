"""FR07 assessment and FR08 memory."""


def _learner_session(learner, prompt_key="structured"):
    sid = learner.start()["session_id"]
    learner.take_control(sid)
    state = learner.state(sid)
    prompts = {
        "structured": "تصرّف كمحرر محتوى عربي. اكتب منشور إطلاق قصيرًا لمقهى الركن يخدم طلاب الجامعة. استخدم الحقائق "
        "المقدَّمة فقط، ولا تتجاوز 70 كلمة، واختم بدعوة واحدة لاتخاذ إجراء. أعد المنشور ثم قائمة بالادعاءات.",
        "weak": "اكتب منشورًا عن مقهى.",
    }
    assert state["lab"]["fixture_id"] == "cafe-launch"
    learner.act(sid, "set_prompt", {"text": prompts[prompt_key]})
    learner.act(sid, "generate_draft")
    saved = learner.act(sid, "save_draft", {"note": "the shorter one"})
    return sid, saved["result"]["artifact_id"]


def test_memory_written_on_end_and_visible_to_learner(learner):
    sid, _ = _learner_session(learner)
    end = learner.post(f"/api/sessions/{sid}/end").json()
    kinds = {m["kind"] for m in end["memory_written"]}
    assert kinds == {"last_successful_task", "next_practice"}
    memory = learner.get("/api/me/memory").json()
    assert {m["kind"] for m in memory} == kinds
    assert all(m["source_session_id"] == sid for m in memory)


def test_deleted_memory_stops_appearing_in_answers(learner):
    sid, _ = _learner_session(learner)
    learner.post(f"/api/sessions/{sid}/end")
    task = next(m for m in learner.get("/api/me/memory").json() if m["kind"] == "last_successful_task")

    sid2 = learner.start()["session_id"]
    assert task["text"] in learner.say(sid2, "ماذا أتدرب الآن؟")["answer"]
    assert learner.delete(f"/api/me/memory/{task['memory_id']}").json() == {"deleted": 1}
    assert task["text"] not in learner.say(sid2, "ماذا أتدرب الآن؟")["answer"]
    learner.delete("/api/me/memory")
    assert "لا توجد ذاكرة" in learner.say(sid2, "ماذا أتدرب الآن؟")["answer"]


def test_tutor_demo_alone_is_not_remembered_as_learner_progress(learner):
    sid = learner.start()["session_id"]
    learner.say(sid, "اعرض البرومبت المنظم")
    assert learner.post(f"/api/sessions/{sid}/end").json()["memory_written"] == []


def test_memory_disabled_writes_nothing(learner):
    assert learner.patch("/api/me", {"memory_enabled": False}).json()["memory_enabled"] is False
    sid, _ = _learner_session(learner)
    assert learner.post(f"/api/sessions/{sid}/end").json()["memory_written"] == []
    assert learner.get("/api/me/memory").json() == []


def test_weak_prompt_memory_records_the_misconception(learner):
    sid, _ = _learner_session(learner, "weak")
    learner.post(f"/api/sessions/{sid}/end")
    memory = {m["kind"]: m["text"] for m in learner.get("/api/me/memory").json()}
    assert "ادعاءات" in memory["misconception"]


def test_structured_submission_passes_checks(learner):
    _, artifact_id = _learner_session(learner)
    artifact = learner.get(f"/api/me/artifacts/{artifact_id}").json()
    content = artifact["content"]
    # Lesson 1 acceptance: request, response, model identifier, timestamp and fixture version are recorded.
    assert content["prompt"] and content["draft_text"] and content["model"] and content["generated_at"]
    assert content["fixture_version"] == "1" and content["created_by"] == "learner"
    sub = learner.post(f"/api/me/artifacts/{artifact_id}/submissions").json()
    assert sub["status"] == "checks_passed", sub["results"]
    assert sub["rubric_id"] == "prompt-checklist" and sub["review_status"] == "not_reviewed"


def test_weak_submission_requests_revision_with_evidence(learner):
    _, artifact_id = _learner_session(learner, "weak")
    sub = learner.post(f"/api/me/artifacts/{artifact_id}/submissions").json()
    failed = {r["criterion_id"]: r["evidence"] for r in sub["results"] if not r["passed"]}
    assert sub["status"] == "revision_requested"
    assert {"prompt_context", "prompt_constraints", "draft_length", "draft_no_unsupported_claims"} <= set(failed)
    assert "20" in failed["draft_no_unsupported_claims"]
    appealed = learner.post(f"/api/me/submissions/{sub['submission_id']}/appeal", {"reason": "The offer was intended"})
    assert appealed.json()["review_status"] == "appeal_requested"


def test_export_contains_prompt_draft_and_checks(learner):
    _, artifact_id = _learner_session(learner)
    r = learner.get(f"/api/me/artifacts/{artifact_id}/export")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/markdown")
    assert "## Prompt" in r.text and "## Draft" in r.text and "Content hash" in r.text
    assert "the shorter one" in r.text


def test_progress_records_lesson_version(learner):
    r = learner.client.put(
        "/api/me/progress/ai-for-everyone/L03", json={"status": "completed"}, headers=learner.headers
    )
    assert r.json()["lesson_version"] == "0.1.0"
    assert learner.get("/api/me/progress").json()[0]["status"] == "completed"
