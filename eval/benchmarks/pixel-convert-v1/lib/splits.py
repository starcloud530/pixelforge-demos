"""Future character-level split. v1 fixtures do not use it."""

from __future__ import annotations

import hashlib


def future_split(character_id: str) -> str:
    """Assign a future character to one split.

    sha256(character_id) first byte mod 10:
    0–1 dev, 2–3 test, 4–9 train.
    Variants that share a character_id stay together.
    """
    first = hashlib.sha256(character_id.encode("utf-8")).digest()[0] % 10
    if first <= 1:
        return "dev"
    if first <= 3:
        return "test"
    return "train"
