from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import Settings
from bot.db.session import session_scope
from bot.handlers.routing import author_from_message, message_datetime, parse_source, source_for_chat
from bot.parsers.redact import redact_card_numbers
from bot.services.ingest import IngestMeta, persist_parse_result

logger = logging.getLogger(__name__)


async def on_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None or not message.text:
        return

    source = source_for_chat(chat.id, settings)
    if source is None:
        return

    author_id, author_name = author_from_message(message)
    message_at = message_datetime(message, settings.timezone)
    result = parse_source(source, message.text, settings, message_at=message_at)

    async with session_scope() as session:
        saved = await persist_parse_result(
            session,
            result,
            IngestMeta(
                source=source,
                telegram_chat_id=chat.id,
                telegram_message_id=message.message_id,
                author_id=author_id,
                author_name=author_name,
                message_at=message_at,
                timezone=settings.timezone,
            ),
        )

    if saved:
        logger.info(
            "saved %s batches from %s by %s",
            saved,
            source,
            redact_card_numbers(author_name or "unknown"),
        )
    else:
        logger.info("no batches parsed from %s (%s)", source, result.skipped_reason)
