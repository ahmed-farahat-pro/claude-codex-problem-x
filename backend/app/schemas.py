"""Request bodies. Learner identity is never part of a request body."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DevLearnerIn(_In):
    display_name: str = Field("Learner", min_length=1, max_length=80)
    language: Literal["ar", "en"] = "ar"


class PreferencesIn(_In):
    language: Literal["ar", "en"] | None = None
    explanation_pref: Literal["short", "detailed"] | None = None
    memory_enabled: bool | None = None


class CreateSessionIn(_In):
    course_id: str = Field(..., max_length=80)
    lesson_id: str = Field(..., max_length=20)


class MessageIn(_In):
    text: str = Field(..., min_length=1, max_length=2000)
    epoch: int


class ActionIn(_In):
    tool: str = Field(..., max_length=40)
    args: dict[str, Any] = Field(default_factory=dict)
    epoch: int
    idempotency_key: str = Field(..., min_length=8, max_length=80)


class ControlIn(_In):
    holder: Literal["tutor", "learner"]


class ProgressIn(_In):
    status: Literal["started", "completed"]


class AppealIn(_In):
    reason: str = Field(..., min_length=3, max_length=1000)
