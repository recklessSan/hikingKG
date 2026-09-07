from datetime import datetime, timezone

from bot.config import Settings
from bot.db.session import create_tables, init_engine, session_scope
from bot.demo import CHAT1_SAMPLES, CHAT2_SAMPLE
from bot.parsers.chat1 import parse_chat1
from bot.parsers.chat2 import parse_chat2
from bot.parsers.redact import contains_pan, redact_card_numbers
from bot.services.ingest import IngestMeta, fetch_batches, persist_parse_result
from bot.services.reports import build_report


def test_redact_spaced_pan():
    text = "Альфа 2200 0000 0000 0001  66.1 хвост"
    redacted = redact_card_numbers(text)
    assert "2200" not in redacted
    assert "[карта скрыта]" in redacted
    assert "хвост" in redacted
    assert not contains_pan(redacted)


async def test_persisted_rows_have_no_pans(tmp_path):
    db_path = tmp_path / "bot.db"
    settings = Settings(database_url=f"sqlite+aiosqlite:///{db_path}", timezone="Europe/Moscow")
    init_engine(settings)
    await create_tables()
    message_at = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)

    async with session_scope() as session:
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

    assert sum(row.card_count for row in rows if row.event_type == "intake") == 11
    assert sum(row.card_count for row in rows if row.event_type == "t_office") == 6
    alfa_intake = [row for row in rows if row.bank == "Альфа" and row.event_type == "intake"]
    assert sum(row.card_count for row in alfa_intake) == 6
    assert any(row.without_lk for row in alfa_intake)
    assert all(row.is_cash for row in alfa_intake)

    for row in rows:
        assert not contains_pan(row.excerpt)
        assert not contains_pan(row.bank)
        assert row.excerpt.find("2200") == -1

    report = build_report(rows, title="Аналитика карт", timezone=settings.timezone)
    assert "Альфа: 6 шт" in report
    assert "ОТП: 5 шт" in report
    assert "Передано в Т-офис" in report
    assert "2200" not in report
    assert not contains_pan(report)
