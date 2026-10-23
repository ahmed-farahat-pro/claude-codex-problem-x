"""Deterministic prompt and draft checks.

These are keyword and count heuristics. They give fast, explainable feedback and drive the deterministic
lab generator; they are not a grade. Creative quality still needs rubric review (PRD section 13).
"""

import re
from dataclasses import asdict, dataclass, field

from . import textnorm
from .content import Fixture

TASK_MARKERS = ("اكتب", "انشي", "صغ ", "حرر", "لخص", "write", "create", "draft", "compose", "summarize")
CONTEXT_MARKERS = ("الحقائق", "حقائق", "سياق", "معلومات", "facts", "context", "details")
AUDIENCE_MARKERS = ("جمهور", "يخدم", "موجه", "موجهه", "للطلاب", "طلاب", "audience", "for students", "readers", "aimed at")
CONSTRAINT_MARKERS = (
    "لا تتجاوز", "لا يتجاوز", "كلمه", "فقط", "لا تضف", "نبره", "بحد اقصي",
    "words", "only", "do not", "don't", "limit", "at most", "tone",
)
FORMAT_MARKERS = ("اعد ", "بصيغه", "صيغه", "قائمه", "علي شكل", "format", "return", "as a list", "bullet", "json", "table")
CTA_REQUEST_MARKERS = ("دعوه", "اجراء", "call to action", "cta")
FACTS_ONLY_MARKERS = (
    "الحقائق المقدمه فقط", "الحقائق فقط", "فقط الحقائق", "لا تضف", "only the supplied facts", "only the facts",
    "only use the facts", "do not add", "don't add",
)
CLAIMS_REQUEST_MARKERS = ("ادعاءات", "الادعاءات", "claims")
CTA_MARKERS = (
    "زورونا", "زوروا", "سجلوا", "سجل الان", "احجزوا", "احجز", "تعالوا", "انضموا", "اطلبوا", "جربوا", "شاركونا",
    "visit", "join", "book", "register", "come ", "order now", "sign up",
)
# Percentages are caught by the unsupported-number check.
OFFER_MARKERS = ("خصم", "تخفيض", "هديه", "عرض خاص", "كوبون", "discount", "free gift", "coupon")
SHORTEN_MARKERS = ("اختصر", "قصر", "اقصر", "shorter", "shorten", "fewer words", "trim")
_LENGTH = re.compile(r"(\d+)\s*(?:كلمه|كلمات|words?)")
_CLAIMS_SPLIT = re.compile(r"^\s*(?:---|ادعاءات تحتاج|claims to verify|claims that need)", re.IGNORECASE | re.MULTILINE)


@dataclass
class PromptAnalysis:
    task: bool
    context: bool
    audience: bool
    constraints: bool
    output_format: bool
    cta_requested: bool
    facts_only: bool
    claims_requested: bool
    max_words: int | None

    def missing(self) -> list[str]:
        return [k for k in ("task", "context", "audience", "constraints", "output_format") if not getattr(self, k)]

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class DraftAnalysis:
    post_text: str
    word_count: int
    max_words: int
    within_limit: bool
    has_cta: bool
    unsupported_numbers: list[str] = field(default_factory=list)
    offer_terms: list[str] = field(default_factory=list)

    @property
    def unsupported_claims(self) -> bool:
        return bool(self.unsupported_numbers or self.offer_terms)

    def as_dict(self) -> dict:
        data = asdict(self)
        data.pop("post_text")
        data["unsupported_claims"] = self.unsupported_claims
        return data


def _max_words(normalized: str) -> int | None:
    match = _LENGTH.search(normalized)
    return int(match.group(1)) if match else None


def analyze_prompt(prompt: str, fixture: Fixture) -> PromptAnalysis:
    text = textnorm.normalize(prompt) + " "
    audience_words = textnorm.content_tokens(fixture.suggested.get("audience", ""))
    return PromptAnalysis(
        task=textnorm.contains_any(text, TASK_MARKERS),
        context=textnorm.contains_any(text, fixture.context_markers) or textnorm.contains_any(text, CONTEXT_MARKERS),
        audience=textnorm.contains_any(text, AUDIENCE_MARKERS)
        or (bool(audience_words) and all(w in textnorm.tokens(text) for w in audience_words)),
        constraints=textnorm.contains_any(text, CONSTRAINT_MARKERS),
        output_format=textnorm.contains_any(text, FORMAT_MARKERS),
        cta_requested=textnorm.contains_any(text, CTA_REQUEST_MARKERS),
        facts_only=textnorm.contains_any(text, FACTS_ONLY_MARKERS),
        claims_requested=textnorm.contains_any(text, CLAIMS_REQUEST_MARKERS),
        max_words=_max_words(text),
    )


def post_section(draft_text: str) -> str:
    """The post itself, without a trailing 'claims to verify' list."""
    match = _CLAIMS_SPLIT.search(draft_text)
    return draft_text[: match.start()].strip() if match else draft_text.strip()


def analyze_draft(draft_text: str, fixture: Fixture, max_words: int) -> DraftAnalysis:
    post = post_section(draft_text)
    normalized = textnorm.normalize(post) + " "
    brief = textnorm.normalize(fixture.brief("ar") + " " + fixture.brief("en"))
    count = textnorm.word_count(post)
    return DraftAnalysis(
        post_text=post,
        word_count=count,
        max_words=max_words,
        within_limit=count <= max_words,
        has_cta=textnorm.contains_any(normalized, CTA_MARKERS),
        unsupported_numbers=sorted({n for n in textnorm.numbers(post) if n not in fixture.allowed_numbers}),
        offer_terms=sorted(
            m for m in OFFER_MARKERS if textnorm.contains_any(normalized, (m,)) and not textnorm.contains_any(brief, (m,))
        ),
    )


def instruction_targets(instruction: str) -> dict:
    text = textnorm.normalize(instruction) + " "
    max_words = _max_words(text)
    if max_words is None and textnorm.contains_any(text, SHORTEN_MARKERS):
        max_words = 35
    return {
        "max_words": max_words,
        "facts_only": textnorm.contains_any(text, FACTS_ONLY_MARKERS)
        or textnorm.contains_any(text, ("احذف الخصم", "بدون خصم", "remove the discount", "no discount")),
        "add_cta": textnorm.contains_any(text, CTA_REQUEST_MARKERS),
    }
