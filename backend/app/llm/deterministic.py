"""Deterministic mode: no paid inference.

TemplateLabGenerator builds drafts from fixture sentences according to which prompt elements are present, so a
weak prompt really produces a long, generic draft with an invented offer and a structured prompt produces a
short factual one. DeterministicTutor is a rule-based stand-in for the reasoning model. Both are clearly
labelled in every response; they exist for regression tests and for building the UI without spending money.
"""

from typing import Any

from .. import checks, textnorm
from ..content import Fixture
from ..retrieval import Hit
from .base import Generation, ModelStep, ToolCall, TurnContext

GENERATOR_MODEL = "deterministic-template-v1"
TUTOR_MODEL = "deterministic-tutor-v1"

# Removal order when a draft must fit a word limit. Calls to action are never removed.
_TRIM_ORDER = ("filler", "fact", "invented", "opening")


def _seg(role: str, text: str) -> dict[str, str]:
    return {"role": role, "text": text}


def compose(segments: list[dict[str, str]]) -> str:
    post = " ".join(s["text"] for s in segments if s["role"] != "claims")
    claims = [s["text"] for s in segments if s["role"] == "claims"]
    return post + ("\n---\n" + claims[0] if claims else "")


def _post_words(segments: list[dict[str, str]]) -> int:
    return textnorm.word_count(" ".join(s["text"] for s in segments if s["role"] != "claims"))


def _fit(segments: list[dict[str, str]], max_words: int) -> list[dict[str, str]]:
    segments = list(segments)
    for role in _TRIM_ORDER:
        while _post_words(segments) > max_words:
            idxs = [i for i, s in enumerate(segments) if s["role"] == role]
            # Keep at least one fact: a shorter post must still say something true.
            if not idxs or (role == "fact" and len(idxs) == 1):
                break
            segments.pop(idxs[-1])
    if _post_words(segments) > max_words:
        body = [i for i, s in enumerate(segments) if s["role"] not in ("cta", "claims")]
        if body:
            i = body[-1]
            excess = _post_words(segments) - max_words
            words = segments[i]["text"].split()
            segments[i] = _seg(segments[i]["role"], " ".join(words[: max(1, len(words) - excess)]))
    return segments


class TemplateLabGenerator:
    model = GENERATOR_MODEL

    def generate(self, *, prompt: str, fixture: Fixture) -> Generation:
        a = checks.analyze_prompt(prompt, fixture)
        t = fixture.template
        if a.audience:
            opening = t["audience_opening"]
        elif a.context:
            opening = t["opening"]
        else:
            opening = t["generic_opening"]
        segments = [_seg("opening", opening)]
        if a.context:
            segments += [_seg("fact", f) for f in t["facts"]]
        if not a.constraints:
            segments += [_seg("filler", f) for f in t["filler"]]
        if not a.facts_only:
            segments.append(_seg("invented", t["invented_claim"]))
        if a.cta_requested:
            segments.append(_seg("cta", t["cta"]))
        if a.max_words:
            segments = _fit(segments, a.max_words)
        if a.claims_requested and a.context:
            segments.append(_seg("claims", t["claims_header"] + "\n" + "\n".join(f"- {c}" for c in t["claims"])))
        return Generation(text=compose(segments), model=self.model, segments=segments)

    def revise(self, *, draft: dict[str, Any], instruction: str, fixture: Fixture) -> Generation:
        segments = [dict(s) for s in (draft.get("segments") or [_seg("opening", checks.post_section(draft["text"]))])]
        targets = checks.instruction_targets(instruction)
        if targets["facts_only"]:
            segments = [s for s in segments if s["role"] not in ("invented", "filler")]
        if targets["add_cta"] and not any(s["role"] == "cta" for s in segments):
            at = next((i for i, s in enumerate(segments) if s["role"] == "claims"), len(segments))
            segments.insert(at, _seg("cta", fixture.template["cta"]))
        if targets["max_words"]:
            segments = _fit(segments, targets["max_words"])
        return Generation(text=compose(segments), model=self.model, segments=segments)


# ---------------------------------------------------------------- tutor

NEXT = ("ماذا اتدرب", "الخطوه التاليه", "ماذا بعد", "what next", "practice next", "next step", "what should i practice")
QUESTION_WORDS = frozenset(
    "كيف لماذا ما ماذا هل متي اين كم why how what when where which who is are can should do does".split()
)
INTENTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("weak_demo", ("مثال ضعيف", "برومبت ضعيف", "مثالا ضعيفا", "weak prompt", "weak example")),
    ("revise", ("اختصر", "قصر المسوده", "حسن المسوده", "عدل المسوده", "اعد صياغه", "revise", "shorten", "make it shorter")),
    ("save", ("احفظ", "save")),
    ("reset", ("اعد ضبط", "اعاده ضبط", "ابدا من جديد", "امسح المختبر", "reset")),
    ("check", ("افحص", "تحقق من المسوده", "راجع المسوده", "check the draft", "check my draft", "verify the draft")),
    ("practice", ("ملخص جديد", "تمرين جديد", "new brief", "practice brief", "another brief")),
    ("demo", ("اعرض", "ارني", "وضح بمثال", "طبق", "نفذ", "show me", "demonstrate", "demo", "do it")),
)
ELEMENT_LABELS = {
    "task": ("المهمة", "task"),
    "context": ("السياق", "context"),
    "audience": ("الجمهور", "audience"),
    "constraints": ("القيود", "constraints"),
    "output_format": ("صيغة المخرجات", "output format"),
}
FIELD_LABELS = {
    "set_brief": ("الملخص", "brief"),
    "set_audience": ("الجمهور", "audience"),
    "set_tone": ("النبرة", "tone"),
    "set_prompt": ("البرومبت", "prompt"),
}
MEMORY_LABELS = {
    "last_successful_task": ("آخر مهمة ناجحة", "Last successful task"),
    "misconception": ("نقطة تحتاج انتباهًا", "Watch out for"),
    "next_practice": ("التمرين التالي", "Next practice"),
}


def detect_intent(text: str) -> str:
    normalized = textnorm.normalize(text) + " "
    if textnorm.contains_any(normalized, NEXT):
        return "next"
    words = normalized.split()
    is_question = normalized.strip().endswith(("?", "؟")) or (bool(words) and words[0] in QUESTION_WORDS)
    if not is_question:
        for intent, markers in INTENTS:
            if textnorm.contains_any(normalized, markers):
                return intent
    return "question"


def _first_sentences(text: str, n: int) -> str:
    parts, current = [], ""
    for ch in text:
        current += ch
        if ch in ".؟?!":
            parts.append(current.strip())
            current = ""
            if len(parts) == n:
                break
    if len(parts) < n and current.strip():
        parts.append(current.strip())
    return " ".join(parts)


class DeterministicTutor:
    model = TUTOR_MODEL

    def start(self, ctx: TurnContext) -> "_Conversation":
        return _Conversation(ctx)


class _Conversation:
    def __init__(self, ctx: TurnContext):
        self.ctx = ctx
        self.intent = detect_intent(ctx.user_text)
        self.acted = False

    def t(self, ar: str, en: str) -> str:
        return en if self.ctx.language == "en" else ar

    def label(self, pair: tuple[str, str]) -> str:
        return self.t(*pair)

    def step(self, tool_results: list[dict[str, Any]]) -> ModelStep:
        if self.acted:
            return self._explain(tool_results)
        step = self._plan()
        self.acted = bool(step.tool_calls)
        return step

    # -- planning

    def _plan(self) -> ModelStep:
        if self.intent == "question":
            return self._answer_question()
        if self.intent == "next":
            return self._answer_next()
        if self.ctx.control == "learner":
            return ModelStep(
                kind="refusal",
                text=self.t(
                    "أنت تتحكم في المختبر الآن، لذلك لن أنفّذ أي خطوة فيه. أعِد التحكم إليّ إذا أردت أن أعرض الخطوة، أو اسألني وسأشرح.",
                    "You have control of the lab, so I will not act in it. Hand control back if you want me to demonstrate, or ask and I will explain.",
                ),
            )
        drafts = self.ctx.lab_state.get("drafts", [])
        fixture = self.ctx.fixture
        if self.intent in ("revise", "save", "check") and not drafts:
            return ModelStep(
                kind="answer",
                text=self.t(
                    "لا توجد مسودة في المختبر بعد. اكتب برومبت ثم اضغط «ولّد مسودة»، أو اطلب مني أن أعرض مثالًا.",
                    "There is no draft in the lab yet. Write a prompt and generate a draft, or ask me to show an example.",
                ),
            )
        calls = {
            "demo": [
                ToolCall("set_audience", {"text": fixture.suggested.get("audience", "")}),
                ToolCall("set_tone", {"text": fixture.suggested.get("tone", "")}),
                ToolCall("set_prompt", {"text": fixture.prompts["structured"]}),
                ToolCall("generate_draft", {}),
                ToolCall("read_output", {}),
            ],
            "weak_demo": [
                ToolCall("set_prompt", {"text": fixture.prompts["weak"]}),
                ToolCall("generate_draft", {}),
                ToolCall("read_output", {}),
            ],
            "revise": [ToolCall("revise_draft", {"instruction": self.ctx.user_text[:500]}), ToolCall("read_output", {})],
            "save": [ToolCall("save_draft", {})],
            "reset": [ToolCall("reset_lab", {})],
            "check": [ToolCall("read_output", {})],
            "practice": [ToolCall("open_lab", {"fixture_id": self.ctx.recipe.get("practice_fixture_id")})],
        }[self.intent]
        return ModelStep(tool_calls=calls)

    def _answer_question(self) -> ModelStep:
        r = self.ctx.retrieval
        if not r.terms or r.is_vague:
            return ModelStep(
                kind="clarify",
                text=self.t(
                    "هل تقصد البرومبت أم المسودة الحالية في المختبر؟ اكتب سؤالك بتفصيل أكثر، مثلًا: «هل تتجاوز المسودة 70 كلمة؟»",
                    "Do you mean the prompt or the current draft in the lab? Ask in a little more detail, for example: “Is the draft over 70 words?”",
                ),
            )
        if not r.in_scope:
            return ModelStep(
                kind="boundary",
                text=self.t(
                    "هذا السؤال خارج محتوى هذه الدورة، ولا أريد أن أخمّن إجابته. أستطيع مساعدتك في كتابة البرومبت ومراجعة المسودات في المختبر.",
                    "That question is outside this course, and I don't want to guess. I can help you write prompts and check drafts in the lab.",
                ),
            )
        detailed = self.ctx.explanation_pref != "short"
        hits: list[Hit] = r.hits[:2] if detailed else r.hits[:1]
        top = hits[0]
        intro = self.t("", "From the lesson (Arabic source):\n")
        text = intro + (top.text if detailed else _first_sentences(top.text, 2))
        if len(hits) > 1:
            text += self.t("\n\nانظر أيضًا: «", "\n\nSee also: “") + hits[1].title + self.t("».", "”.")
        return ModelStep(kind="answer", text=text, cited=[h.passage_id for h in hits])

    def _answer_next(self) -> ModelStep:
        memory = {m["kind"]: m for m in self.ctx.memory}
        if not memory:
            suggestion = self.ctx.recipe.get("next_practice", {}).get(self.ctx.language, "")
            return ModelStep(
                kind="answer",
                text=self.t("لا توجد ذاكرة تعلم محفوظة لك. اقتراح الدرس: ", "You have no saved learning memory. The lesson suggests: ")
                + suggestion,
            )
        lines = [self.t("من ذاكرة التعلم الخاصة بك:", "From your learning memory:")]
        for kind, pair in MEMORY_LABELS.items():
            if kind in memory:
                lines.append(f"- {self.label(pair)}: {memory[kind]['text']}")
        return ModelStep(kind="answer", text="\n".join(lines))

    # -- explaining observed results

    def _explain(self, results: list[dict[str, Any]]) -> ModelStep:
        lines: list[str] = []
        for r in results:
            if r["status"] != "succeeded":
                lines.append(
                    self.t(
                        f"✗ الخطوة {r['tool']} لم تنجح ({r.get('error_category')}). لم أفترض نجاحها وتوقفت هنا.",
                        f"✗ Step {r['tool']} did not succeed ({r.get('error_category')}). I did not assume it worked and stopped here.",
                    )
                )
                break
            lines.extend(self._describe(r))
        lines.append(self._closing(results))
        return ModelStep(kind="answer", text="\n".join(line for line in lines if line))

    def _describe(self, r: dict[str, Any]) -> list[str]:
        tool, result = r["tool"], r.get("result") or {}
        if tool in FIELD_LABELS:
            return [
                self.t(
                    f"✓ حدّثتُ حقل «{FIELD_LABELS[tool][0]}» وتحققتُ من ظهوره في المختبر.",
                    f"✓ I set the {FIELD_LABELS[tool][1]} field and checked it shows in the lab.",
                )
            ]
        if tool in ("generate_draft", "revise_draft"):
            draft = result.get("draft", {})
            return [self.t(f"✓ ولّدتُ المسودة رقم {draft.get('number')}.", f"✓ I generated draft {draft.get('number')}.")]
        if tool == "read_output":
            return self._describe_checks(result)
        if tool == "save_draft":
            return [self.t(f"✓ حفظتُ المسودة في أعمالك ({result.get('artifact_id')}).", f"✓ I saved the draft to your work ({result.get('artifact_id')}).")]
        if tool == "reset_lab":
            return [self.t("✓ أعدتُ المختبر إلى الملخص الأصلي. أعمالك المحفوظة لم تتغير.", "✓ I reset the lab to the original brief. Your saved work is unchanged.")]
        if tool == "open_lab":
            return [self.t(f"✓ فتحتُ ملخصًا جديدًا: {result.get('business_name')}.", f"✓ I opened a new brief: {result.get('business_name')}.")]
        return []

    def _describe_checks(self, result: dict[str, Any]) -> list[str]:
        d, p = result.get("draft_checks", {}), result.get("prompt_checks", {})
        ok, bad = "✓", "✗"
        lines = [
            self.t(
                f"{ok if d.get('within_limit') else bad} الطول: {d.get('word_count')} كلمة من {d.get('max_words')}.",
                f"{ok if d.get('within_limit') else bad} Length: {d.get('word_count')} of {d.get('max_words')} words.",
            ),
            self.t(
                f"{ok if d.get('has_cta') else bad} دعوة لاتخاذ إجراء.",
                f"{ok if d.get('has_cta') else bad} Call to action.",
            ),
        ]
        unsupported = d.get("unsupported_numbers", []) + d.get("offer_terms", [])
        if unsupported:
            lines.append(
                self.t(
                    f"{bad} ادعاءات غير موجودة في الملخص: {'، '.join(unsupported)}. يجب حذفها قبل النشر.",
                    f"{bad} Claims missing from the brief: {', '.join(unsupported)}. Remove them before publishing.",
                )
            )
        else:
            lines.append(self.t(f"{ok} لا أرقام أو عروض غير موجودة في الملخص.", f"{ok} No numbers or offers missing from the brief."))
        missing = [k for k in ELEMENT_LABELS if not p.get(k, True)]
        if missing:
            names = "، ".join(self.label(ELEMENT_LABELS[k]) for k in missing) if self.ctx.language != "en" else ", ".join(
                self.label(ELEMENT_LABELS[k]) for k in missing
            )
            lines.append(self.t(f"{bad} ينقص البرومبت: {names}.", f"{bad} The prompt is missing: {names}."))
        return lines

    def _closing(self, results: list[dict[str, Any]]) -> str:
        if any(r["status"] != "succeeded" for r in results):
            return self.t("يمكنك إعادة المحاولة أو إعادة ضبط المختبر.", "You can retry or reset the lab.")
        return {
            "demo": self.t(
                "دورك الآن: اضغط «تولَّ التحكم»، غيّر قيدًا واحدًا، ثم ولّد مسودة جديدة وقارن بين النسختين.",
                "Your turn: take control, change one constraint, generate again and compare the two versions.",
            ),
            "weak_demo": self.t(
                "هذا مثال على برومبت ضعيف. اطلب مني «اعرض البرومبت المنظم» لنقارن النتيجتين.",
                "That was a weak prompt. Ask me to “show the structured prompt” so we can compare.",
            ),
            "revise": self.t("قارن النسختين: ما الذي تغيّر، وهل بقيت الحقائق كما هي؟", "Compare both versions: what changed, and are the facts unchanged?"),
            "practice": self.t("حاول بنفسك: اكتب برومبت منظمًا لهذا الملخص.", "Try it yourself: write a structured prompt for this brief."),
        }.get(self.intent, "")
