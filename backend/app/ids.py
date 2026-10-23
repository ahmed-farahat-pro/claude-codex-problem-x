"""Opaque identifiers. Never derive meaning from them."""

import secrets


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(12)}"
