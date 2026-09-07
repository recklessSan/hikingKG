from __future__ import annotations

import re

# 13–19 digits with optional spaces or dashes — typical PAN layout.
_PAN_RE = re.compile(r"(?<!\d)(?:\d[ \t-]*){13,19}(?!\d)")
_SPACED_PAN_RE = re.compile(
    r"(?<!\d)(\d{4}(?:[ \t-]+\d{4}){2,4})(?!\d)"
)


def redact_card_numbers(text: str, replacement: str = "[карта скрыта]") -> str:
    """Remove PAN-like digit sequences before any persistence or logging."""
    if not text:
        return text
    redacted = _SPACED_PAN_RE.sub(replacement, text)
    redacted = _PAN_RE.sub(replacement, redacted)
    return redacted


def looks_like_card_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if _SPACED_PAN_RE.search(stripped) or _PAN_RE.search(stripped):
        return True
    return False


def contains_pan(text: str) -> bool:
    if not text:
        return False
    return bool(_SPACED_PAN_RE.search(text) or _PAN_RE.search(text))
