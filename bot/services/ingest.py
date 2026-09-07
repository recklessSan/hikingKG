from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import CardBatch, PhoneCheck
from bot.parsers.base import ParsedBatch, ParseResult
from bot.parsers.redact import contains_pan, redact_card_numbers
from bot.services.phones import persist_phone_checks


def merge_batches(batches: list[ParsedBatch]) -> list[ParsedBatch]:
    merged: dict[tuple[str, str], ParsedBatch] = {}
    for batch in batches:
        key = (batch.bank_slug, batch.event_type)
        existing = merged.get(key)
        if existing is None:
            merged[key] = batch
            continue
        existing.card_count += batch.card_count
        existing.is_cash = existing.is_cash or batch.is_cash
        existing.without_lk = existing.without_lk or batch.without_lk
        existing.is_urgent = existing.is_urgent or batch.is_urgent
        existing.has_deposit = existing.has_deposit or batch.has_deposit
        existing.lk_access_at = existing.lk_access_at or batch.lk_access_at
        existing.work_at = existing.work_at or batch.work_at
        existing.batch_ref = existing.batch_ref or batch.batch_ref
        if batch.excerpt and batch.excerpt not in existing.excerpt:
            existing.excerpt = f"{existing.excerpt}\n{batch.excerpt}".strip()
        seen = {item.e164 for item in existing.phones}
        for phone in batch.phones:
            if phone.e164 not in seen:
                existing.phones.append(phone)
                seen.add(phone.e164)
    return list(merged.values())


@dataclass(slots=True)
class IngestMeta:
    source: str
    telegram_chat_id: int
    telegram_message_id: int
    author_id: int | None
    author_name: str | None
    message_at: datetime
    timezone: str = "Europe/Moscow"


async def persist_parse_result(session: AsyncSession, result: ParseResult, meta: IngestMeta) -> int:
    old_ids = list(
        await session.scalars(
            select(CardBatch.id).where(
                CardBatch.telegram_chat_id == meta.telegram_chat_id,
                CardBatch.telegram_message_id == meta.telegram_message_id,
            )
        )
    )
    if old_ids:
        await session.execute(delete(PhoneCheck).where(PhoneCheck.batch_id.in_(old_ids)))
    await session.execute(
        delete(CardBatch).where(
            CardBatch.telegram_chat_id == meta.telegram_chat_id,
            CardBatch.telegram_message_id == meta.telegram_message_id,
        )
    )
    if not result.batches:
        return 0

    tz = ZoneInfo(meta.timezone)
    message_at = meta.message_at
    if message_at.tzinfo is None:
        message_at = message_at.replace(tzinfo=tz)

    saved = 0
    for batch in merge_batches(result.batches):
        excerpt = redact_card_numbers(batch.excerpt or "")
        if contains_pan(excerpt):
            excerpt = "[данные скрыты]"
        row = CardBatch(
            source=result.source,
            event_type=batch.event_type,
            telegram_chat_id=meta.telegram_chat_id,
            telegram_message_id=meta.telegram_message_id,
            author_id=meta.author_id,
            author_name=meta.author_name,
            message_at=message_at,
            report_date=batch.report_date or message_at.astimezone(tz).date(),
            bank=batch.bank,
            bank_slug=batch.bank_slug,
            card_count=batch.card_count,
            is_cash=batch.is_cash,
            without_lk=batch.without_lk,
            is_urgent=batch.is_urgent,
            batch_ref=batch.batch_ref,
            lk_access_at=batch.lk_access_at,
            work_at=batch.work_at,
            has_deposit=batch.has_deposit,
            excerpt=excerpt[:500],
            phone_count=len(batch.phones),
        )
        session.add(row)
        await session.flush()
        known, unknown = await persist_phone_checks(session, row.id, batch.phones)
        row.phones_known = known
        row.phones_unknown = unknown
        saved += 1
    await session.flush()
    return saved


async def fetch_batches(
    session: AsyncSession,
    *,
    date_from=None,
    date_to=None,
    event_type: str | None = None,
) -> list[CardBatch]:
    stmt = select(CardBatch).order_by(CardBatch.report_date.asc(), CardBatch.id.asc())
    if date_from is not None:
        stmt = stmt.where(CardBatch.report_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(CardBatch.report_date <= date_to)
    if event_type is not None:
        stmt = stmt.where(CardBatch.event_type == event_type)
    result = await session.execute(stmt)
    return list(result.scalars().all())
