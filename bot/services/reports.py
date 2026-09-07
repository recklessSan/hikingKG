from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from bot.db.models import CardBatch


def _fmt_date(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def build_report(
    batches: list[CardBatch],
    *,
    title: str,
    date_from: date | None = None,
    date_to: date | None = None,
    timezone: str = "Europe/Moscow",
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
    lines.append(
        f"Итого поступлений: {sum(row.card_count for row in intake)} шт"
    )
    lines.append(
        f"Итого в Т-офис: {sum(row.card_count for row in t_office)} шт"
    )
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

    if authors:
        top = ", ".join(
            f"{name} {count}"
            for name, count in sorted(authors.items(), key=lambda item: -item[1])[:5]
        )
        lines.append(f"авторы: {top}")
    return lines


def period_for_today(timezone: str) -> tuple[date, date]:
    today = datetime.now(ZoneInfo(timezone)).date()
    return today, today


def period_for_week(timezone: str) -> tuple[date, date]:
    today = datetime.now(ZoneInfo(timezone)).date()
    start = today - timedelta(days=6)
    return start, today
