"""The Gemini path with a fake client that returns real SDK response objects (no network, no key)."""

import pytest

types = pytest.importorskip("google.genai.types")

from app.llm.gemini import GeminiLabGenerator, GeminiTutor  # noqa: E402


def _response(parts, prompt_tokens=100, output_tokens=20):
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=parts))],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=prompt_tokens, candidates_token_count=output_tokens
        ),
    )


class FakeModels:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_content(self, *, model, contents, config):
        self.calls.append({"model": model, "contents": list(contents) if isinstance(contents, list) else contents,
                           "config": config})
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses):
        self.models = FakeModels(responses)


def test_tool_loop_citations_and_usage(make_app, new_learner):
    client = FakeClient(
        [
            # 1. tutor asks to set the prompt and generate
            _response([
                types.Part(function_call=types.FunctionCall(id="c1", name="set_prompt",
                                                            args={"text": "اكتب منشورًا قصيرًا لمقهى الركن"})),
                types.Part(function_call=types.FunctionCall(id="c2", name="generate_draft", args={})),
            ]),
            # 2. the lab generator produces the draft
            _response([types.Part(text="مقهى الركن يفتح الأحد. زورونا!")], 50, 10),
            # 3. tutor explains, citing one retrieved passage and one it was never given
            _response([types.Part(text="ولّدتُ مسودة قصيرة [P:L03-constraints] [P:L99-made-up].")]),
        ]
    )
    app = make_app(tutor=GeminiTutor(client, "gemini-test"), generator=GeminiLabGenerator(client, "gemini-test"))
    learner = new_learner(app)
    sid = learner.start()["session_id"]
    turn = learner.say(sid, "ما هي القيود؟ ثم اعرض مثالًا")

    assert turn["status"] == "completed"
    assert [(a["tool"], a["status"]) for a in turn["actions"]] == [
        ("set_prompt", "succeeded"), ("generate_draft", "succeeded")
    ]
    assert turn["answer"] == "ولّدتُ مسودة قصيرة."
    assert [s["passage_id"] for s in turn["sources"]] == ["L03-constraints"]  # invented citation dropped

    lab = learner.state(sid)["lab"]
    assert lab["drafts"][0]["model"] == "gemini-test" and lab["drafts"][0]["created_by"] == "tutor"
    usage = learner.state(sid)["usage"]
    assert usage["model_input_tokens"] == 250 and usage["model_output_tokens"] == 50

    first, _, third = client.models.calls
    declared = {d.name for d in first["config"].tools[0].function_declarations}
    assert declared == {"open_lab", "read_lab_state", "set_brief", "set_audience", "set_tone", "set_prompt",
                        "generate_draft", "revise_draft", "read_output", "save_draft", "reset_lab"}
    assert first["config"].automatic_function_calling.disable is True
    tool_turn = third["contents"][-1]
    assert tool_turn.role == "tool"
    assert [p.function_response.name for p in tool_turn.parts] == ["set_prompt", "generate_draft"]
    assert tool_turn.parts[1].function_response.response["status"] == "succeeded"


def test_provider_failure_is_reported_not_invented(make_app, new_learner):
    class Failing:
        class models:
            @staticmethod
            def generate_content(**kwargs):
                raise ConnectionError("network down")

    app = make_app(tutor=GeminiTutor(Failing(), "gemini-test"), generator=GeminiLabGenerator(Failing(), "gemini-test"))
    learner = new_learner(app)
    sid = learner.start()["session_id"]
    turn = learner.say(sid, "سؤال")
    assert turn["status"] == "failed" and turn["error_category"] == "provider_error"
    learner.take_control(sid)
    learner.act(sid, "set_prompt", {"text": "اكتب"})
    gen = learner.act(sid, "generate_draft")
    assert gen["status"] == "failed" and gen["error_category"] == "provider_error"
    assert learner.state(sid)["lab"]["drafts"] == []
