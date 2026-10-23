"""Bounded tool manifest (PRD section 11, permission model).

The tutor gets exactly these typed actions. No shell, no arbitrary code, no free navigation, no database access.
A new course adds a reviewed manifest instead of widening this one.
"""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ToolError(Exception):
    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category
        self.message = message


class _Args(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class NoArgs(_Args):
    pass


class OpenLabArgs(_Args):
    fixture_id: str | None = Field(None, description="Fixture to load. Omit to reload the lesson's main fixture.")


class BriefArgs(_Args):
    text: str = Field(..., max_length=1200, description="Business brief shown in the lab.")


class AudienceArgs(_Args):
    text: str = Field(..., max_length=200, description="Who the post is for.")


class ToneArgs(_Args):
    text: str = Field(..., max_length=60, description="Tone of voice, for example ودود or رسمي.")


class PromptArgs(_Args):
    text: str = Field(..., max_length=2000, description="The full prompt that will be sent to the generator.")


class ReviseArgs(_Args):
    instruction: str = Field(..., min_length=1, max_length=500, description="One specific revision request.")
    draft_id: str | None = Field(None, description="Draft to revise. Omit for the latest draft.")


class DraftRefArgs(_Args):
    draft_id: str | None = Field(None, description="Draft to read. Omit for the latest draft.")


class SaveArgs(_Args):
    draft_id: str | None = Field(None, description="Draft to save. Omit for the latest draft.")
    title: str | None = Field(None, max_length=120, description="Optional title for the saved work.")
    note: str | None = Field(None, max_length=500, description="Optional reason for choosing this draft.")


@dataclass(frozen=True)
class ToolSpec:
    name: str
    args_model: type[_Args]
    description: str
    mutates: bool
    # Learners may always read and save their own work, even while the tutor holds control.
    learner_without_control: bool = False


TOOLS: dict[str, ToolSpec] = {
    spec.name: spec
    for spec in (
        ToolSpec("open_lab", OpenLabArgs, "Load a lesson fixture into the Content Studio lab.", True),
        ToolSpec("read_lab_state", NoArgs, "Read the current lab fields and drafts.", False, True),
        ToolSpec("set_brief", BriefArgs, "Replace the business brief field.", True),
        ToolSpec("set_audience", AudienceArgs, "Set the audience field.", True),
        ToolSpec("set_tone", ToneArgs, "Set the tone field.", True),
        ToolSpec("set_prompt", PromptArgs, "Set the prompt field.", True),
        ToolSpec("generate_draft", NoArgs, "Generate a draft from the current prompt field.", True),
        ToolSpec("revise_draft", ReviseArgs, "Generate a revised draft from an existing draft and one instruction.", True),
        ToolSpec("read_output", DraftRefArgs, "Read a generated draft and its rule-based checks.", False, True),
        ToolSpec("save_draft", SaveArgs, "Save a draft to the learner's work.", True, True),
        ToolSpec("reset_lab", NoArgs, "Restore the active fixture and clear fields and drafts. Saved work is kept.", True),
    )
}


def validate_call(name: str, args: dict[str, Any] | None, allowed: list[str]) -> tuple[ToolSpec, _Args]:
    spec = TOOLS.get(name)
    if spec is None:
        raise ToolError("unknown_tool", f"Unknown tool: {name}")
    if name not in allowed:
        raise ToolError("not_allowed", f"Tool {name} is not allowed in this lesson")
    if args is not None and not isinstance(args, dict):
        raise ToolError("validation", "Tool arguments must be an object")
    try:
        return spec, spec.args_model.model_validate(args or {})
    except ValidationError as exc:
        details = "; ".join(f"{'.'.join(map(str, e['loc'])) or 'args'}: {e['msg']}" for e in exc.errors())
        raise ToolError("validation", details) from exc


def _clean_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Pydantic JSON schema reduced to the portable subset model providers accept."""
    properties = {}
    for key, prop in schema.get("properties", {}).items():
        if "anyOf" in prop:  # Optional[str] -> str
            prop = {**next(p for p in prop["anyOf"] if p.get("type") != "null"), "description": prop.get("description")}
        properties[key] = {k: v for k, v in prop.items() if k in ("type", "description", "maxLength", "minLength") and v}
    return {"type": "object", "properties": properties, "required": schema.get("required", [])}


def manifest(allowed: list[str] | None = None) -> list[dict[str, Any]]:
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "mutates": spec.mutates,
            "parameters": _clean_schema(spec.args_model.model_json_schema()),
        }
        for spec in TOOLS.values()
        if allowed is None or spec.name in allowed
    ]
