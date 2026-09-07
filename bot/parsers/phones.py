from __future__ import annotations

import re

from bot.parsers.redact import looks_like_card_line

# Trailing metric like "66.1" is ignored; it is not stored.
_TRAILING_METRIC_RE = re.compile(r"\s+\d+[.,]\d+\s*$")


def normalize_phone(raw: str | None) -> str | None:
    """Return 7XXXXXXXXXX or None. 13–19 digit PAN-like values are rejected."""
    if not raw:
        return None
    cleaned = _TRAILING_METRIC_RE.sub("", raw.strip())
    if looks_like_card_line(cleaned):
        return None
    digits = re.sub(r"\D", "", cleaned)
    if len(digits) >= 13:
        return None
    if len(digits) == 11 and digits[0] in {"7", "8"}:
        return "7" + digits[1:]
    if len(digits) == 10 and digits[0] == "9":
        return "7" + digits
    return None


def format_phone(e164: str) -> str:
    if len(e164) == 11 and e164.startswith("7"):
        return f"+7 {e164[1:4]} {e164[4:7]}-{e164[7:9]}-{e164[9:11]}"
    return e164


def extract_phone_from_line(line: str) -> str | None:
    return normalize_phone(line)
