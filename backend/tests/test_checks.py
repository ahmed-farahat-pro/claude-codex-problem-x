from pathlib import Path

import pytest

from app import checks, textnorm
from app.content import ContentRegistry
from app.llm.deterministic import TemplateLabGenerator, detect_intent

CONTENT = Path(__file__).resolve().parents[2] / "content"


@pytest.fixture(scope="module")
def course():
    return ContentRegistry.load(CONTENT).course("ai-for-everyone")


@pytest.mark.parametrize("fixture_id", ["cafe-launch", "bookstore-evening"])
def test_weak_prompt_produces_a_failing_draft(course, fixture_id):
    fixture = course.fixtures[fixture_id]
    prompt = checks.analyze_prompt(fixture.prompts["weak"], fixture)
    assert prompt.task and prompt.missing() == ["context", "audience", "constraints", "output_format"]
    draft = TemplateLabGenerator().generate(prompt=fixture.prompts["weak"], fixture=fixture)
    d = checks.analyze_draft(draft.text, fixture, 70)
    assert d.word_count > 70
    assert d.unsupported_claims
    assert not d.has_cta


@pytest.mark.parametrize("fixture_id", ["cafe-launch", "bookstore-evening"])
def test_structured_prompt_passes_every_check(course, fixture_id):
    fixture = course.fixtures[fixture_id]
    prompt = checks.analyze_prompt(fixture.prompts["structured"], fixture)
    assert prompt.missing() == []
    assert prompt.facts_only and prompt.cta_requested and prompt.max_words == 70
    draft = TemplateLabGenerator().generate(prompt=fixture.prompts["structured"], fixture=fixture)
    d = checks.analyze_draft(draft.text, fixture, 70)
    assert d.within_limit and d.has_cta and not d.unsupported_claims
    assert checks.post_section(draft.text) != draft.text  # the claims list is separate from the post


def test_revision_to_35_words_keeps_call_to_action_and_facts(course):
    fixture = course.fixtures["cafe-launch"]
    gen = TemplateLabGenerator()
    first = gen.generate(prompt=fixture.prompts["structured"], fixture=fixture)
    revised = gen.revise(
        draft={"text": first.text, "segments": first.segments}, instruction="اختصر المسودة إلى 35 كلمة", fixture=fixture
    )
    d = checks.analyze_draft(revised.text, fixture, 35)
    assert d.within_limit and d.has_cta and not d.unsupported_claims
    assert any(s["role"] == "fact" for s in revised.segments)


def test_marker_matching_respects_word_starts():
    assert textnorm.contains_any(textnorm.normalize("اذكر الجمهور"), ("جمهور",))
    assert not textnorm.contains_any(textnorm.normalize("قواعد الكتابة "), ("اعد ",))


def test_normalization_handles_arabic_forms():
    assert textnorm.normalize("أَعِدّ المسوّدة") == "اعد المسوده"
    assert textnorm.numbers("من ٧ حتى 11") == ["7", "11"]
    assert textnorm.word_count("مرحبا — بكم  في 2026") == 4


@pytest.mark.parametrize(
    "text,intent",
    [
        ("اعرض البرومبت المنظم", "demo"),
        ("اعرض لي مثالا ضعيفا", "weak_demo"),
        ("اختصر المسودة", "revise"),
        ("احفظ المسودة", "save"),
        ("كيف أحفظ عملي؟", "question"),
        ("ماذا أتدرب الآن؟", "next"),
        ("Show me", "demo"),
        ("What is a call to action?", "question"),
    ],
)
def test_intent_detection(text, intent):
    assert detect_intent(text) == intent
