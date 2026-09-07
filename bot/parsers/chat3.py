from __future__ import annotations

from datetime import datetime

from bot.parsers.base import ParseResult
from bot.parsers.chat1 import parse_chat1
from bot.parsers.chat2 import parse_chat2


def parse_chat3(
    text: str,
    *,
    mode: str = "auto",
    timezone: str = "Europe/Moscow",
    message_at: datetime | None = None,
) -> ParseResult:
    """Third chat format was not provided; auto-detect chat1 then chat2."""
    mode = (mode or "auto").lower()
    if mode == "chat1":
        result = parse_chat1(text, timezone=timezone)
        result.source = "chat3"
        return result
    if mode == "chat2":
        result = parse_chat2(text, message_at=message_at)
        result.source = "chat3"
        return result

    chat1 = parse_chat1(text, timezone=timezone)
    if chat1.batches:
        chat1.source = "chat3"
        return chat1
    chat2 = parse_chat2(text, message_at=message_at)
    if chat2.batches:
        chat2.source = "chat3"
        return chat2
    return ParseResult(source="chat3", skipped_reason="unrecognized_format")
