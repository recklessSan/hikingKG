from __future__ import annotations

import re
from dataclasses import dataclass

_ALIASES: list[tuple[tuple[str, ...], str, str]] = [
    (("альфабанк", "альфа-банк", "альфа", "alfa", "alpha"), "Альфа", "alfa"),
    (("тинькофф", "тиньков", "тинь", "tinkoff", "tbank", "t-банк", "т-банк", "тбанк"), "Тинькофф", "tinkoff"),
    (("сбербанк", "сбер", "sber"), "Сбер", "sber"),
    (("газпромбанк", "газпром", "gpb"), "Газпромбанк", "gpb"),
    (("отпбанк", "отп", "otp"), "ОТП", "otp"),
    (("озонбанк", "озон", "ozon"), "Озон", "ozon"),
    (("псб", "psb"), "ПСБ", "psb"),
    (("втб", "vtb"), "ВТБ", "vtb"),
    (("мтсбанк", "мтс", "mts"), "МТС", "mts"),
    (("юмани", "юmoney", "yumoney"), "ЮMoney", "yumoney"),
]


def _fold(value: str) -> str:
    return re.sub(r"[\s.\-]+", "", value.casefold())


@dataclass(frozen=True, slots=True)
class Bank:
    name: str
    slug: str


def normalize_bank(raw: str | None) -> Bank | None:
    if not raw:
        return None
    folded = _fold(raw)
    if not folded:
        return None
    for aliases, name, slug in _ALIASES:
        for alias in aliases:
            if folded == alias or folded.startswith(alias):
                return Bank(name=name, slug=slug)
    cleaned = re.sub(r"\s+", " ", raw).strip(" :.-")
    if not cleaned:
        return None
    return Bank(name=cleaned.capitalize(), slug=_fold(cleaned)[:32] or "unknown")
