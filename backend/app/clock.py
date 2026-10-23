"""Single source of time so tests can control it."""

import time
from datetime import datetime, timezone


def now() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now().isoformat(timespec="milliseconds")


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def monotonic_ms() -> int:
    return int(time.monotonic() * 1000)
