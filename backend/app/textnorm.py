"""Arabic-aware text normalization shared by retrieval, checks and the deterministic tutor."""

import re
import unicodedata
from functools import lru_cache

_TASHKEEL = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭ]")
_TATWEEL = "ـ"
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_ALEF = re.compile("[إأآٱ]")
_TOKEN = re.compile(r"\w+", re.UNICODE)

# Definite article and attached prepositions. Longest first.
_PREFIXES = ("وال", "بال", "كال", "فال", "لل", "ال")

STOPWORDS = frozenset(
    """
    ما ماذا من في على الي عن هل هو هي هذا هذه ذلك تلك كيف لماذا متي اين كم او ثم مع كل قد لا لم لن ان انا انت
    نحن هم التي الذي كان كانت يكون اذا به بها له لها عند بين غير اي يا و ف ب ل ك اريد ممكن يمكن يجب فقط جدا
    الان يوم اليوم امس غدا لي لك
    a an the is are was were what who whom how why when where which do does did i you me my we our to of in on
    for and or it its this that these those should can could would will be with about please tell now today
    yesterday tomorrow
    """.split()
)

# Words that carry no answerable topic on their own ("is this good?").
VAGUE = frozenset("جيد جيده صح صحيح تمام مناسب good ok okay right fine correct".split())


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = _TASHKEEL.sub("", text).replace(_TATWEEL, "")
    text = text.translate(_DIGITS)
    text = _ALEF.sub("ا", text)
    text = text.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    return text.lower()


def stem(token: str) -> str:
    for prefix in _PREFIXES:
        if token.startswith(prefix) and len(token) - len(prefix) >= 2:
            return token[len(prefix):]
    return token


def tokens(text: str) -> list[str]:
    return [stem(t) for t in _TOKEN.findall(normalize(text))]


def content_tokens(text: str) -> list[str]:
    """Normalized tokens with stopwords removed, de-duplicated in order."""
    seen: list[str] = []
    for raw in _TOKEN.findall(normalize(text)):
        if raw in STOPWORDS:
            continue
        token = stem(raw)
        if token in STOPWORDS or token in seen:
            continue
        seen.append(token)
    return seen


@lru_cache(maxsize=1024)
def _marker_pattern(marker: str) -> re.Pattern[str]:
    # Match at a word start, allowing attached Arabic prefixes (الجمهور, للطلاب, وبدون).
    return re.compile(r"(?<!\w)(?:وال|بال|كال|فال|لل|ال|و|ب|ل|ك|ف)?" + re.escape(normalize(marker)))


def contains_any(normalized_text: str, markers: list[str] | tuple[str, ...]) -> bool:
    return any(_marker_pattern(m).search(normalized_text) for m in markers)


def word_count(text: str) -> int:
    """Whitespace-delimited words that contain at least one letter or digit."""
    return sum(1 for w in text.split() if any(ch.isalnum() for ch in w))


def numbers(text: str) -> list[str]:
    return re.findall(r"\d+", normalize(text))
