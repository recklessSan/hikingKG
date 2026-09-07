from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from bot.db.models import CardBatch
from bot.parsers.phones import format_phone


def _fmt_date(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def build_report(
    batches: list[CardBatch],
    *,
    title: str,
    date_from: date | None = None,
    date_to: date | None = None,
    timezone: str = "Europe/Moscow",
    unknown_phones: list[str] | None = None,
) -> str:
    tz = ZoneInfo(timezone)
    generated = datetime.now(tz).strftime("%d.%m.%Y %H:%M")

    period = ""
    if date_from and date_to:
        if date_from == date_to:
            period = f"за {_fmt_date(date_from)}"
        else:
            period = f"с {_fmt_date(date_from)} по {_fmt_date(date_to)}"
    elif date_from:
        period = f"с {_fmt_date(date_from)}"

    intake = [row for row in batches if row.event_type == "intake"]
    t_office = [row for row in batches if row.event_type == "t_office"]

    lines = [f"📊 {title}".strip()]
    if period:
        lines[0] = f"📊 {title} {period}".strip()
    lines.append(f"сформировано: {generated}")
    lines.append("")
    lines.extend(_section("Поступления", intake))
    lines.append("")
    lines.extend(_section("Передано в Т-офис", t_office))
    lines.append("")
    lines.append(f"Итого поступлений: {sum(row.card_count for row in intake)} шт")
    lines.append(f"Итого в Т-офис: {sum(row.card_count for row in t_office)} шт")
    lines.extend(_phones_block(batches, unknown_phones=unknown_phones))
    return "\n".join(lines)


def _section(title: str, rows: list[CardBatch]) -> list[str]:
    if not rows:
        return [f"{title}: нет данных"]

    by_bank: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    authors: dict[str, int] = defaultdict(int)
    for row in rows:
        stats = by_bank[row.bank]
        stats["count"] += row.card_count
        stats["batches"] += 1
        stats["phones"] += row.phone_count or 0
        stats["known"] += row.phones_known or 0
        stats["unknown"] += row.phones_unknown or 0
        if row.is_cash:
            stats["cash"] += row.card_count
        if row.without_lk:
            stats["no_lk"] += row.card_count
        if row.author_name:
            authors[row.author_name] += row.card_count

    lines = [f"{title}:"]
    for bank in sorted(by_bank, key=lambda name: (-by_bank[name]["count"], name)):
        stats = by_bank[bank]
        extra = []
        if stats["cash"]:
            extra.append(f"кэш {stats['cash']}")
        if stats["no_lk"]:
            extra.append(f"без ЛК {stats['no_lk']}")
        suffix = f" ({', '.join(extra)})" if extra else ""
        lines.append(f"• {bank}: {stats['count']} шт{suffix}")
        if stats["phones"]:
            lines.append(
                f"  телефоны: {stats['phones']} (в базе {stats['known']}, нет {stats['unknown']})"
            )

    if authors:
        top = ", ".join(
            f"{name} {count}"
            for name, count in sorted(authors.items(), key=lambda item: -item[1])[:5]
        )
        lines.append(f"авторы: {top}")
    return lines


def _phones_block(batches: list[CardBatch], unknown_phones: list[str] | None) -> list[str]:
    phones = sum(row.phone_count or 0 for row in batches)
    if not phones:
        return []
    known = sum(row.phones_known or 0 for row in batches)
    unknown = sum(row.phones_unknown or 0 for row in batches)
    lines = [
        "",
        "Проверка телефонов:",
        f"разобрано: {phones}",
        f"есть в базе: {known}",
        f"нет в базе: {unknown}",
    ]
    if unknown_phones:
        preview = unknown_phones[:20]
        lines.append("не найдены: " + ", ".join(preview))
        if len(unknown_phones) > 20:
            lines.append(f"… и ещё {len(unknown_phones) - 20}")
    return lines


def period_for_today(timezone: str) -> tuple[date, date]:
    today = datetime.now(ZoneInfo(timezone)).date()
    return today, today


def period_for_week(timezone: str) -> tuple[date, date]:
    today = datetime.now(ZoneInfo(timezone)).date()
    start = today - timedelta(days=6)
    return start, today


def format_check_result(phone: str, label: str | None, found: bool) -> str:
    pretty = format_phone(phone)
    if found:
        extra = f" ({label})" if label else ""
        return f"{pretty}: есть в базе{extra}"
    return f"{pretty}: нет в базе"
