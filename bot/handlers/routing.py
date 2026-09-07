from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from bot.config import Settings
from bot.parsers.chat1 import parse_chat1
from bot.parsers.chat2 import parse_chat2
from bot.parsers.chat3 import parse_chat3
from bot.parsers.base import ParseResult


def source_for_chat(chat_id: int, settings: Settings) -> str | None:
    for source, configured in settings.chat_ids().items():
        if configured == chat_id:
            return source
    return None


def parse_source(
    source: str,
    text: str,
    settings: Settings,
    message_at: datetime | None = None,
) -> ParseResult:
    if source == "chat1":
        return parse_chat1(text, timezone=settings.timezone)
    if source == "chat2":
        return parse_chat2(text, message_at=message_at)
    if source == "chat3":
        return parse_chat3(
            text,
            mode=settings.chat_3_mode,
            timezone=settings.timezone,
            message_at=message_at,
        )
    return ParseResult(source=source, skipped_reason="unknown_source")


def author_from_message(message) -> tuple[int | None, str | None]:
    user = message.from_user
    if user is not None:
        name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
        if not name:
            name = user.username
        return user.id, name
    sender = getattr(message, "sender_chat", None)
    if sender is not None:
        return sender.id, sender.title
    return None, None


def message_datetime(message, timezone: str) -> datetime:
    tz = ZoneInfo(timezone)
    dt = message.date
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt
