from datetime import datetime
from zoneinfo import ZoneInfo

from bot.parsers.chat1 import parse_chat1
from bot.parsers.phones import normalize_phone
from bot.parsers.redact import contains_pan


def test_chat1_parses_phones_and_skips_pans():
    text = """Альфа: 4 шт  КЭШ   F1701092026 ❗️

+7 900 111-22-31
8 (900) 111-22-32
79001112233
9001112235
2200 0000 0000 0001  66.1
"""
    result = parse_chat1(text)
    batch = result.batches[0]
    assert batch.bank == "Альфа"
    assert batch.card_count == 4
    assert batch.is_cash is True
    assert batch.is_urgent is True
    assert batch.batch_ref == "F1701092026"
    assert [item.e164 for item in batch.phones] == [
        "79001112231",
        "79001112232",
        "79001112233",
        "79001112235",
    ]
    assert not contains_pan(batch.excerpt)
    assert not any("2200" in (item.raw or "") for item in batch.phones)


def test_chat1_otp_cash():
    text = """ОТП: 5 шт   КЭШ

+7 900 111 22 41
8 900 111 22 42
79001112243
+7 900 111-22-44
9001112245
"""
    batch = parse_chat1(text).batches[0]
    assert batch.bank == "ОТП"
    assert batch.card_count == 5
    assert len(batch.phones) == 5


def test_chat1_without_lk_and_schedule():
    text = """Альфа: 2 шт БЕЗ ЛК  КЭШ

+7 900 111-22-31
8 900 111-22-36

Вход в лк в 19:40 02.09.2026 + внесение + в работу в 19:40 03.09.2026
"""
    batch = parse_chat1(text).batches[0]
    tz = ZoneInfo("Europe/Moscow")
    assert batch.card_count == 2
    assert batch.without_lk is True
    assert batch.has_deposit is True
    assert batch.lk_access_at == datetime(2026, 9, 2, 19, 40, tzinfo=tz)
    assert batch.work_at == datetime(2026, 9, 3, 19, 40, tzinfo=tz)
    assert len(batch.phones) == 2


def test_normalize_rejects_pan_like_values():
    assert normalize_phone("2200 0000 0000 0001") is None
    assert normalize_phone("2200153688173955") is None
    assert normalize_phone("+7 900 111-22-31") == "79001112231"
    assert normalize_phone("8 900 111 22 32") == "79001112232"
    assert normalize_phone("9001112233") == "79001112233"
