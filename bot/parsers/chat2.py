from __future__ import annotations

import re
from datetime import datetime

from bot.parsers.banks import normalize_bank
from bot.parsers.base import ParsedBatch, ParseResult
from bot.parsers.redact import looks_like_card_line, redact_card_numbers

_DATE_RE = re.compile(r"^\s*(\d{2}\.\d{2}\.\d{4})\s*$")
_COUNT_BANK_RE = re.compile(
    r"^(?P<count>\d+)\s+(?P<bank>[^\d]+?)(?:\s*\(.*\))?\s*$",
    re.IGNORECASE,
)
_T_OFFICE_RE = re.compile(
    r"^передано\s+в\s+[тt][\s\-]*о?фис",
    re.IGNORECASE,
)


def _fold_line(line: str) -> str:
    compact = re.sub(r"\s+", " ", line).strip().casefold()
    compact = compact.replace("ё", "е")
    return compact


def _is_section_header(line: str) -> bool:
    if not line or line[0].isdigit() or _COUNT_BANK_RE.match(line):
        return False
    compact = re.sub(r"\s+", " ", line).strip()
    if len(compact) > 80:
        return False
    letters = re.sub(r"[^А-ЯA-ZЁа-яa-zё]", "", compact)
    if not letters:
        return False
    upper_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters)
    folded = _fold_line(line)
    return upper_ratio >= 0.7 or _T_OFFICE_RE.match(folded) is not None


def _is_t_office_header(line: str) -> bool:
    return _T_OFFICE_RE.match(_fold_line(line)) is not None


def parse_chat2(text: str, *, message_at: datetime | None = None) -> ParseResult:
    lines = text.replace("\r\n", "\n").split("\n")
    report_date = message_at.date() if message_at else None
    in_section = False
    batches: list[ParsedBatch] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line or looks_like_card_line(line):
            continue

        date_match = _DATE_RE.match(line)
        if date_match and not in_section:
            report_date = datetime.strptime(date_match.group(1), "%d.%m.%Y").date()
            continue

        if _is_section_header(line):
            in_section = _is_t_office_header(line)
            continue

        if not in_section:
            continue

        if line in {"0", "-", "—"}:
            continue

        match = _COUNT_BANK_RE.match(line)
        if not match:
            continue
        count = int(match.group("count"))
        if count <= 0:
            continue
        bank = normalize_bank(match.group("bank"))
        if bank is None:
            continue
        batches.append(
            ParsedBatch(
                bank=bank.name,
                bank_slug=bank.slug,
                card_count=count,
                event_type="t_office",
                report_date=report_date,
                excerpt=redact_card_numbers(line),
            )
        )

    if not batches:
        return ParseResult(source="chat2", skipped_reason="no_t_office_rows")
    return ParseResult(source="chat2", batches=batches)
