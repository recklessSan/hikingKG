from datetime import datetime, timezone

from bot.parsers.chat2 import parse_chat2
from bot.parsers.chat3 import parse_chat3

CHAT2 = """05.09.2026

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


def test_chat2_takes_only_t_office():
    result = parse_chat2(CHAT2, message_at=datetime(2026, 9, 7, tzinfo=timezone.utc))
    assert len(result.batches) == 1
    batch = result.batches[0]
    assert batch.bank == "Альфа"
    assert batch.card_count == 6
    assert batch.event_type == "t_office"
    assert batch.report_date.isoformat() == "2026-09-05"


def test_chat2_multiple_t_office_banks():
    text = """ПЕРЕДАНО В Т-ОФИС
3 СБЕР
2 ОТП
0
"""
    result = parse_chat2(text)
    assert {(b.bank, b.card_count) for b in result.batches} == {("Сбер", 3), ("ОТП", 2)}


def test_chat3_auto_detects_chat1():
    result = parse_chat3("ОТП: 5 шт КЭШ\n2201 0000 0000 0001  10.0")
    assert result.source == "chat3"
    assert result.batches[0].bank == "ОТП"
    assert result.batches[0].event_type == "intake"


def test_chat3_auto_detects_chat2():
    result = parse_chat3("ПЕРЕДАНО В Т-ОФИС\n4 ТИНЬ")
    assert result.source == "chat3"
    assert result.batches[0].bank == "Тинькофф"
    assert result.batches[0].card_count == 4
    assert result.batches[0].event_type == "t_office"
