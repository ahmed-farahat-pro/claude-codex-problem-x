"""Content Studio lab: server-owned state, typed tools, observed verification.

Each tool runs in two phases so slow model work never holds the database write lock:
  prepare() validates against the current state and does any generation (no writes),
  Prepared.apply() turns the latest state into the new state inside the write transaction.
After the commit the session service re-reads the state and calls Prepared.verify() on what it observed.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .. import checks, clock
from ..content import Course, Fixture
from ..ids import new_id
from ..llm.base import Generation, LabGenerator, ProviderError
from .tools import ToolError

FIELDS = {"set_brief": "brief", "set_audience": "audience", "set_tone": "tone", "set_prompt": "prompt"}


@dataclass
class Prepared:
    apply: Callable[[dict[str, Any]], tuple[dict[str, Any], dict[str, Any]]] | None = None
    result: dict[str, Any] | None = None  # read-only tools answer immediately
    verify: Callable[[dict[str, Any], dict[str, Any]], bool] = lambda observed, result: True
    generation: Generation | None = None
    save: dict[str, Any] | None = field(default=None)  # draft to persist as a learner artifact

    @property
    def read_only(self) -> bool:
        return self.apply is None and self.save is None


def public_draft(draft: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in draft.items() if k != "segments"}


def public_state(state: dict[str, Any]) -> dict[str, Any]:
    return {**state, "drafts": [public_draft(d) for d in state.get("drafts", [])]}


class ContentStudio:
    def __init__(self, course: Course, recipe: dict[str, Any], generator: LabGenerator):
        self.course = course
        self.recipe = recipe
        self.generator = generator
        template = course.lab_templates[recipe["lab_template_id"]]
        self.template_id = template["template_id"]
        self.template_version = template["version"]
        self.limits = template["limits"]
        self.allowed_fixtures = [f for f in (recipe.get("fixture_id"), recipe.get("practice_fixture_id")) if f]
        self.rubric = course.rubrics[recipe["rubric_id"]]

    def fixture(self, fixture_id: str) -> Fixture:
        return self.course.fixtures[fixture_id]

    def initial_state(self, fixture_id: str | None = None) -> dict[str, Any]:
        fixture = self.fixture(fixture_id or self.recipe["fixture_id"])
        return {
            "template_id": self.template_id,
            "template_version": self.template_version,
            "fixture_id": fixture.fixture_id,
            "fixture_version": fixture.version,
            "business_name": fixture.business_name("ar"),
            "brief": fixture.brief("ar"),
            "audience": "",
            "tone": "",
            "prompt": "",
            "drafts": [],
        }

    def health_check(self, state: dict[str, Any]) -> bool:
        fixture = self.fixture(state["fixture_id"])
        return state["brief"] == fixture.brief("ar") and state["template_id"] == self.template_id

    def checks_for(self, draft: dict[str, Any]) -> dict[str, Any]:
        fixture = self.fixture(draft["fixture_id"])
        return {
            "prompt_checks": checks.analyze_prompt(draft.get("prompt", ""), fixture).as_dict(),
            "draft_checks": checks.analyze_draft(draft["text"], fixture, self.rubric.get("max_words", 70)).as_dict(),
        }

    @staticmethod
    def _find_draft(state: dict[str, Any], draft_id: str | None) -> dict[str, Any]:
        drafts = state.get("drafts", [])
        if not drafts:
            raise ToolError("no_draft", "There is no draft in the lab yet")
        if draft_id is None:
            return drafts[-1]
        for draft in drafts:
            if draft["draft_id"] == draft_id:
                return draft
        raise ToolError("not_found", f"Draft {draft_id} not found in this lab")

    def _new_draft(self, state: dict[str, Any], gen: Generation, prompt: str, **extra: Any) -> dict[str, Any]:
        return {
            "draft_id": new_id("drf"),
            "number": len(state.get("drafts", [])) + 1,
            "text": gen.text,
            "model": gen.model,
            "prompt": prompt,
            "fixture_id": state["fixture_id"],
            "fixture_version": state["fixture_version"],
            "created_at": clock.now_iso(),
            "segments": gen.segments,
            **extra,
        }

    def _generate(self, fn: Callable[[], Generation]) -> Generation:
        try:
            gen = fn()
        except ProviderError as exc:
            raise ToolError("provider_error", str(exc)) from exc
        if not gen.text.strip():
            raise ToolError("provider_error", "The generator returned an empty draft")
        return gen

    def prepare(self, tool: str, args: Any, state: dict[str, Any], actor: str) -> Prepared:
        if tool == "read_lab_state":
            return Prepared(result=public_state(state))

        if tool == "read_output":
            draft = self._find_draft(state, args.draft_id)
            return Prepared(result={"draft": public_draft(draft), **self.checks_for(draft)})

        if tool in FIELDS:
            name = FIELDS[tool]
            text = args.text

            def apply_field(latest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
                return {**latest, name: text}, {"field": name}

            def verify_field(observed: dict[str, Any], result: dict[str, Any]) -> bool:
                result["observed"] = observed[name]
                return observed[name] == text

            return Prepared(apply=apply_field, verify=verify_field)

        if tool in ("open_lab", "reset_lab"):
            fixture_id = getattr(args, "fixture_id", None) or (
                state["fixture_id"] if tool == "reset_lab" else self.recipe["fixture_id"]
            )
            if fixture_id not in self.allowed_fixtures:
                raise ToolError("not_allowed", f"Fixture {fixture_id} is not part of this lesson")
            fresh = self.initial_state(fixture_id)

            def apply_fixture(latest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
                return fresh, {"fixture_id": fixture_id, "business_name": fresh["business_name"]}

            def verify_fixture(observed: dict[str, Any], result: dict[str, Any]) -> bool:
                return observed == fresh and self.health_check(observed)

            return Prepared(apply=apply_fixture, verify=verify_fixture)

        if tool == "generate_draft":
            prompt = state.get("prompt", "").strip()
            if not prompt:
                raise ToolError("validation", "The prompt field is empty")
            self._check_draft_limit(state)
            fixture = self.fixture(state["fixture_id"])
            gen = self._generate(lambda: self.generator.generate(prompt=prompt, fixture=fixture))
            return self._draft_prepared(gen, prompt, created_by=actor)

        if tool == "revise_draft":
            source = self._find_draft(state, args.draft_id)
            self._check_draft_limit(state)
            fixture = self.fixture(source["fixture_id"])
            gen = self._generate(lambda: self.generator.revise(draft=source, instruction=args.instruction, fixture=fixture))
            return self._draft_prepared(
                gen, source["prompt"], created_by=actor, parent_draft_id=source["draft_id"], instruction=args.instruction
            )

        if tool == "save_draft":
            draft = self._find_draft(state, args.draft_id)
            return Prepared(save={"draft": draft, "title": args.title, "note": args.note})

        raise ToolError("unknown_tool", f"Content Studio does not implement {tool}")

    def _check_draft_limit(self, state: dict[str, Any]) -> None:
        if len(state.get("drafts", [])) >= self.limits["max_drafts"]:
            raise ToolError("limit", "Draft limit reached for this session. Save your best draft or reset the lab.")

    def _draft_prepared(self, gen: Generation, prompt: str, **extra: Any) -> Prepared:
        holder: dict[str, Any] = {}

        def apply_draft(latest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
            draft = self._new_draft(latest, gen, prompt, **extra)
            holder["draft"] = draft
            return {**latest, "drafts": [*latest.get("drafts", []), draft]}, {"draft": public_draft(draft)}

        def verify_draft(observed: dict[str, Any], result: dict[str, Any]) -> bool:
            wanted = holder["draft"]["draft_id"]
            return any(d["draft_id"] == wanted and d["text"].strip() for d in observed.get("drafts", []))

        return Prepared(apply=apply_draft, verify=verify_draft, generation=gen)
