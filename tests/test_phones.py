from bot.parsers.phones import format_phone, normalize_phone


def test_phone_formats():
    assert normalize_phone("+7 (900) 111-22-33") == "79001112233"
    assert normalize_phone("8-900-111-22-33") == "79001112233"
    assert format_phone("79001112233") == "+7 900 111-22-33"


def test_phone_with_trailing_metric_still_parses():
    assert normalize_phone("79001112233  12.5") == "79001112233"
