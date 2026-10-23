"""Model-facing interfaces. The coordinator never talks to a provider SDK directly."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from ..content import Fixture
from ..retrieval import RetrievalResult


class ProviderError(Exception):
    """The model provider failed. The turn reports it honestly instead of inventing output."""


@dataclass
class Generation:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    # Deterministic drafts keep their sentence roles so revisions can preserve facts.
    segments: list[dict[str, str]] | None = None


class LabGenerator(Protocol):
    def generate(self, *, prompt: str, fixture: Fixture) -> Generation: ...

    def revise(self, *, draft: dict[str, Any], instruction: str, fixture: Fixture) -> Generation: ...


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]
    call_id: str | None = None


@dataclass
class ModelStep:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    # Passage ids the answer relies on. The coordinator keeps only ids that were actually retrieved.
    cited: list[str] = field(default_factory=list)
    kind: str = "answer"  # answer | boundary | clarify | refusal
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class TurnContext:
    user_text: str
    language: str
    explanation_pref: str
    display_name: str
    memory: list[dict[str, Any]]
    lesson: dict[str, Any]
    recipe: dict[str, Any]
    fixture: Fixture
    lab_state: dict[str, Any]
    control: str
    retrieval: RetrievalResult
    history: list[dict[str, Any]]
    allowed_tools: list[str]


class TutorConversation(Protocol):
    def step(self, tool_results: list[dict[str, Any]]) -> ModelStep:
        """Return the next step. tool_results are the observed results of the previous step's tool calls."""
        ...


class TutorModel(Protocol):
    def start(self, ctx: TurnContext) -> TutorConversation: ...
