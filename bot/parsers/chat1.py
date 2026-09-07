from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from bot.parsers.banks import normalize_bank
from bot.parsers.base import ParsedBatch, ParsedPhone, ParseResult
from bot.parsers.phones import extract_phone_from_line
from bot.parsers.redact import looks_like_card_line, redact_card_numbers

_HEADER_RE = re.compile(
    r"^(?P<bank>[^\d\n:]{2,40})\s*:\s*(?P<count>\d+)\s*шт\b(?P<rest>.*)$",
    re.IGNORECASE,
)
_BATCH_REF_RE = re.compile(r"\b([A-Za-zА-Яа-яЁё]\d{5,})\b")
_LK_RE = re.compile(
    r"вход\s+в\s+лк\s+в\s+(?P<lk_time>\d{1,2}:\d{2})\s+(?P<lk_date>\d{2}\.\d{2}\.\d{4})",
    re.IGNORECASE,
)
_WORK_RE = re.compile(
    r"в\s+работу\s+в\s+(?P<work_time>\d{1,2}:\d{2})\s+(?P<work_date>\d{2}\.\d{2}\.\d{4})",
    re.IGNORECASE,
)


def _parse_dt(time_str: str, date_str: str, tz: ZoneInfo) -> datetime:
    return datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M").replace(tzinfo=tz)


def parse_chat1(text: str, *, timezone: str = "Europe/Moscow") -> ParseResult:
    tz = ZoneInfo(timezone)
    lines = text.replace("\r\n", "\n").split("\n")
    batches: list[ParsedBatch] = []
    current: ParsedBatch | None = None
    footer_lk: datetime | None = None
    footer_work: datetime | None = None
    footer_deposit = False
    footer_excerpt = ""

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        header = _HEADER_RE.match(line)
        if header:
            bank = normalize_bank(header.group("bank"))
            if bank is None:
                continue
            rest = header.group("rest") or ""
            rest_upper = rest.casefold()
            ref_match = _BATCH_REF_RE.search(rest)
            current = ParsedBatch(
                bank=bank.name,
                bank_slug=bank.slug,
                card_count=int(header.group("count")),
                event_type="intake",
                is_cash="кэш" in rest_upper or "cash" in rest_upper,
                without_lk="без лк" in rest_upper,
                is_urgent="❗" in rest or "❗️" in rest,
                batch_ref=ref_match.group(1) if ref_match else None,
                excerpt=redact_card_numbers(line),
            )
            batches.append(current)
            continue

        folded = line.casefold()
        if "вход в лк" in folded or "в работу" in folded:
            footer_excerpt = redact_card_numbers(line)
            lk_match = _LK_RE.search(line)
            work_match = _WORK_RE.search(line)
            if lk_match:
                footer_lk = _parse_dt(lk_match.group("lk_time"), lk_match.group("lk_date"), tz)
            if work_match:
                footer_work = _parse_dt(work_match.group("work_time"), work_match.group("work_date"), tz)
            footer_deposit = "внесение" in folded
            continue

        phone = extract_phone_from_line(line)
        if phone and current is not None:
            if all(item.e164 != phone for item in current.phones):
                current.phones.append(ParsedPhone(e164=phone, raw=line))
            continue

        if looks_like_card_line(line):
            continue

    if not batches:
        return ParseResult(source="chat1", skipped_reason="no_bank_header")

    for batch in batches:
        batch.lk_access_at = footer_lk
        batch.work_at = footer_work
        batch.has_deposit = footer_deposit
        if footer_excerpt:
            batch.excerpt = f"{batch.excerpt}\n{footer_excerpt}".strip()

    return ParseResult(source="chat1", batches=batches)
