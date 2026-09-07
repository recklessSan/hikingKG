from datetime import datetime
from zoneinfo import ZoneInfo

from bot.parsers.chat1 import parse_chat1
from bot.parsers.redact import contains_pan


def test_chat1_cash_batch_ignores_card_lines():
    text = """Альфа: 4 шт  КЭШ   F1701092026 ❗️

2200 0000 0000 0001  66.1
2200 0000 0000 0002  51.2
2200 0000 0000 0003  1.2
2200 0000 0000 0004  3.1
"""
    result = parse_chat1(text)
    assert result.skipped_reason is None
    assert len(result.batches) == 1
    batch = result.batches[0]
    assert batch.bank == "Альфа"
    assert batch.card_count == 4
    assert batch.is_cash is True
    assert batch.without_lk is False
    assert batch.is_urgent is True
    assert batch.batch_ref == "F1701092026"
    assert batch.event_type == "intake"
    assert not contains_pan(batch.excerpt)


def test_chat1_otp_cash():
    text = """ОТП: 5 шт   КЭШ

2201 0000 0000 0001  37.7
2201 0000 0000 0002  70.6
2201 0000 0000 0003  1.4
2201 0000 0000 0004  43.3
2201 0000 0000 0005  69.2
"""
    batch = parse_chat1(text).batches[0]
    assert batch.bank == "ОТП"
    assert batch.card_count == 5
    assert batch.is_cash is True
    assert batch.batch_ref is None


def test_chat1_without_lk_and_schedule():
    text = """Альфа: 2 шт БЕЗ ЛК  КЭШ

2200 0000 0000 0008  66.6
2200 0000 0000 0009  65.1

Вход в лк в 19:40 02.09.2026 + внесение + в работу в 19:40 03.09.2026
"""
    batch = parse_chat1(text).batches[0]
    tz = ZoneInfo("Europe/Moscow")
    assert batch.card_count == 2
    assert batch.without_lk is True
    assert batch.is_cash is True
    assert batch.has_deposit is True
    assert batch.lk_access_at == datetime(2026, 9, 2, 19, 40, tzinfo=tz)
    assert batch.work_at == datetime(2026, 9, 3, 19, 40, tzinfo=tz)
    assert "Вход в лк" in batch.excerpt
    assert not contains_pan(batch.excerpt)
