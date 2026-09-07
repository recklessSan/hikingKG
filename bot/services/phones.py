from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import PhoneCheck, PhoneDirectory
from bot.parsers.base import ParsedPhone
from bot.parsers.phones import format_phone, normalize_phone


async def upsert_directory_phone(
    session: AsyncSession,
    raw: str,
    *,
    label: str | None = None,
    source: str = "manual",
) -> PhoneDirectory | None:
    phone = normalize_phone(raw)
    if phone is None:
        return None
    row = await session.scalar(select(PhoneDirectory).where(PhoneDirectory.phone == phone))
    if row is None:
        row = PhoneDirectory(phone=phone, label=label, source=source, is_active=True)
        session.add(row)
        await session.flush()
        return row
    row.is_active = True
    row.source = source or row.source
    if label:
        row.label = label
    await session.flush()
    return row


async def import_phones_csv(session: AsyncSession, path: str | Path, *, source: str = "csv") -> int:
    file_path = Path(path)
    if not file_path.is_file():
        return 0
    imported = 0
    with file_path.open(encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(2048)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        if reader.fieldnames:
            fields = [name.strip().casefold() for name in reader.fieldnames]
            has_header = "phone" in fields or "телефон" in fields or "number" in fields
        else:
            has_header = False
        if not has_header:
            handle.seek(0)
            for raw_line in handle:
                raw = raw_line.strip()
                if not raw or raw.startswith("#"):
                    continue
                if await upsert_directory_phone(session, raw.split(",")[0], source=source):
                    imported += 1
            return imported
        phone_key = next(
            (name for name in reader.fieldnames if name.strip().casefold() in {"phone", "телефон", "number", "номер"}),
            reader.fieldnames[0],
        )
        label_key = next(
            (name for name in reader.fieldnames if name.strip().casefold() in {"label", "метка", "name", "имя", "comment"}),
            None,
        )
        for row in reader:
            raw = (row.get(phone_key) or "").strip()
            label = (row.get(label_key) or "").strip() if label_key else ""
            if await upsert_directory_phone(session, raw, label=label or None, source=source):
                imported += 1
    return imported


async def lookup_directory(session: AsyncSession, phone: str) -> PhoneDirectory | None:
    return await session.scalar(
        select(PhoneDirectory).where(
            PhoneDirectory.phone == phone,
            PhoneDirectory.is_active.is_(True),
        )
    )


async def persist_phone_checks(
    session: AsyncSession,
    batch_id: int,
    phones: list[ParsedPhone],
) -> tuple[int, int]:
    known = 0
    unknown = 0
    for item in phones:
        directory = await lookup_directory(session, item.e164)
        is_known = directory is not None
        if is_known:
            known += 1
        else:
            unknown += 1
        session.add(
            PhoneCheck(
                batch_id=batch_id,
                phone=item.e164,
                is_known=is_known,
                directory_label=directory.label if directory else None,
            )
        )
    await session.flush()
    return known, unknown


async def fetch_unknown_phones(session: AsyncSession, batch_ids: list[int]) -> list[str]:
    if not batch_ids:
        return []
    rows = await session.scalars(
        select(PhoneCheck.phone)
        .where(PhoneCheck.batch_id.in_(batch_ids), PhoneCheck.is_known.is_(False))
        .distinct()
        .order_by(PhoneCheck.phone)
    )
    return [format_phone(phone) for phone in rows]


def directory_count_text(total: int) -> str:
    return f"в справочнике {total} номеров"
