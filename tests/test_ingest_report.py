from datetime import datetime, timezone
from pathlib import Path

from bot.config import Settings
from bot.db.models import PhoneCheck
from bot.db.session import create_tables, init_engine, session_scope
from bot.demo import CHAT1_SAMPLES, CHAT2_SAMPLE
from bot.parsers.chat1 import parse_chat1
from bot.parsers.chat2 import parse_chat2
from bot.parsers.phones import normalize_phone
from bot.parsers.redact import contains_pan, redact_card_numbers
from bot.services.ingest import IngestMeta, fetch_batches, persist_parse_result
from bot.services.phones import fetch_unknown_phones, import_phones_csv, lookup_directory, upsert_directory_phone
from bot.services.reports import build_report
from sqlalchemy import select


def test_redact_spaced_pan():
    text = "Альфа 2200 0000 0000 0001  66.1 хвост"
    redacted = redact_card_numbers(text)
    assert "2200" not in redacted
    assert "[карта скрыта]" in redacted
    assert "хвост" in redacted
    assert not contains_pan(redacted)


async def test_persisted_rows_check_phones_against_directory(tmp_path):
    db_path = tmp_path / "bot.db"
    settings = Settings(database_url=f"sqlite+aiosqlite:///{db_path}", timezone="Europe/Moscow")
    init_engine(settings)
    await create_tables()
    message_at = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    phones_file = Path("phones.example.csv")

    async with session_scope() as session:
        await import_phones_csv(session, phones_file)
        for index, sample in enumerate(CHAT1_SAMPLES, start=1):
            await persist_parse_result(
                session,
                parse_chat1(sample, timezone=settings.timezone),
                IngestMeta(
                    source="chat1",
                    telegram_chat_id=-1001234567890,
                    telegram_message_id=index,
                    author_id=42,
                    author_name="Оператор",
                    message_at=message_at,
                    timezone=settings.timezone,
                ),
            )
        await persist_parse_result(
            session,
            parse_chat2(CHAT2_SAMPLE, message_at=message_at),
            IngestMeta(
                source="chat2",
                telegram_chat_id=-1001234567891,
                telegram_message_id=99,
                author_id=7,
                author_name="Склад",
                message_at=message_at,
                timezone=settings.timezone,
            ),
        )
        rows = await fetch_batches(session)
        unknown = await fetch_unknown_phones(session, [row.id for row in rows])
        checks = list((await session.scalars(select(PhoneCheck))).all())

    assert sum(row.card_count for row in rows if row.event_type == "intake") == 11
    assert sum(row.card_count for row in rows if row.event_type == "t_office") == 6
    assert sum(row.phone_count for row in rows) == 11
    assert sum(row.phones_known for row in rows) == 7
    assert sum(row.phones_unknown for row in rows) == 4
    assert checks
    assert all(len(item.phone) == 11 and item.phone.startswith("7") for item in checks)
    assert unknown

    for row in rows:
        assert not contains_pan(row.excerpt)
        assert row.excerpt.find("2200") == -1

    report = build_report(
        rows,
        title="Аналитика",
        timezone=settings.timezone,
        unknown_phones=unknown,
    )
    assert "Альфа: 6 шт" in report
    assert "ОТП: 5 шт" in report
    assert "Проверка телефонов" in report
    assert "2200" not in report
    assert not contains_pan(report)


async def test_manual_directory_lookup(tmp_path):
    db_path = tmp_path / "lookup.db"
    settings = Settings(database_url=f"sqlite+aiosqlite:///{db_path}")
    init_engine(settings)
    await create_tables()
    async with session_scope() as session:
        saved = await upsert_directory_phone(session, "+7 999 111-22-33", label="склад")
        assert saved is not None
        found = await lookup_directory(session, normalize_phone("8 999 111 22 33"))
        missing = await lookup_directory(session, "79991112200")
    assert found is not None
    assert found.label == "склад"
    assert missing is None
