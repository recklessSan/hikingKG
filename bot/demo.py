from __future__ import annotations

from datetime import datetime, timezone

from bot.config import Settings
from bot.db.session import create_tables, init_engine, session_scope
from bot.parsers.chat1 import parse_chat1
from bot.parsers.chat2 import parse_chat2
from bot.parsers.redact import contains_pan
from bot.services.ingest import IngestMeta, persist_parse_result
from bot.services.reports import build_report

CHAT1_SAMPLES = [
    """Альфа: 4 шт  КЭШ   F1701092026 ❗️

2200 0000 0000 0001  66.1
2200 0000 0000 0002  51.2
2200 0000 0000 0003  1.2
2200 0000 0000 0004  3.1
""",
    """ОТП: 5 шт   КЭШ

2201 0000 0000 0001  37.7
2201 0000 0000 0002  70.6
2201 0000 0000 0003  1.4
2201 0000 0000 0004  43.3
2201 0000 0000 0005  69.2
""",
    """Альфа: 2 шт БЕЗ ЛК  КЭШ

2200 0000 0000 0008  66.6
2200 0000 0000 0009  65.1

Вход в лк в 19:40 02.09.2026 + внесение + в работу в 19:40 03.09.2026
""",
]

CHAT2_SAMPLE = """05.09.2026

ПРИНЯТО ОТ КУРЬЕРА
1 ПСБ
2 ВТБ
2 ОЗОН
1 АЛЬФА
2 ТИНЬ
6 СБЕР
18 ОТП

ПЕРЕДАНО В Т-ОФИС
6 АЛЬФА

ПЕРЕДАНО В Р-ОФИС
0

РЕЗЕРВ (ГОТОВЫ К ПЕРЕДАЧЕ)
10 АЛЬФА (пластик)

НА ПРОВЕРКЕ
1 ПСБ
2 ВТБ
2 ОЗОН
1 АЛЬФА
2 ТИНЬ
6 СБЕР
18 ОТП
"""


async def run_demo(database_url: str = "sqlite+aiosqlite:///:memory:") -> int:
    settings = Settings(database_url=database_url, timezone="Europe/Moscow")
    init_engine(settings)
    await create_tables()
    message_at = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)

    async with session_scope() as session:
        for index, sample in enumerate(CHAT1_SAMPLES, start=1):
            result = parse_chat1(sample, timezone=settings.timezone)
            await persist_parse_result(
                session,
                result,
                IngestMeta(
                    source="chat1",
                    telegram_chat_id=-1001,
                    telegram_message_id=index,
                    author_id=42,
                    author_name="Оператор",
                    message_at=message_at,
                    timezone=settings.timezone,
                ),
            )
        result = parse_chat2(CHAT2_SAMPLE, message_at=message_at)
        await persist_parse_result(
            session,
            result,
            IngestMeta(
                source="chat2",
                telegram_chat_id=-1002,
                telegram_message_id=10,
                author_id=7,
                author_name="Склад",
                message_at=message_at,
                timezone=settings.timezone,
            ),
        )
        from bot.services.ingest import fetch_batches

        batches = await fetch_batches(session)

    for row in batches:
        blob = " ".join(
            str(part)
            for part in [
                row.bank,
                row.excerpt,
                row.batch_ref,
                row.author_name,
            ]
            if part
        )
        if contains_pan(blob):
            print("ошибка: в БД попал номер карты")
            return 1

    report = build_report(
        batches,
        title="Демо-аналитика карт",
        date_from=datetime(2026, 9, 5).date(),
        date_to=datetime(2026, 9, 5).date(),
        timezone=settings.timezone,
    )
    print(report)
    print("\nномеров карт в базе нет")
    return 0
