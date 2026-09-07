from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(slots=True)
class ParsedPhone:
    e164: str
    raw: str = ""


@dataclass(slots=True)
class ParsedBatch:
    bank: str
    bank_slug: str
    card_count: int
    event_type: str
    is_cash: bool = False
    without_lk: bool = False
    is_urgent: bool = False
    batch_ref: str | None = None
    lk_access_at: datetime | None = None
    work_at: datetime | None = None
    has_deposit: bool = False
    report_date: date | None = None
    excerpt: str = ""
    phones: list[ParsedPhone] = field(default_factory=list)


@dataclass(slots=True)
class ParseResult:
    source: str
    batches: list[ParsedBatch] = field(default_factory=list)
    skipped_reason: str | None = None
