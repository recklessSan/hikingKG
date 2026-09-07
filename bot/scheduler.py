from __future__ import annotations

import logging

from telegram.ext import ContextTypes

from bot.config import Settings
from bot.db.session import session_scope
from bot.services.ingest import fetch_batches
from bot.services.phones import fetch_unknown_phones
from bot.services.reports import build_report, period_for_today

logger = logging.getLogger(__name__)


async def send_daily_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if settings.admin_chat_id is None:
        logger.warning("ADMIN_CHAT_ID is not set, skip scheduled report")
        return
    date_from, date_to = period_for_today(settings.timezone)
    async with session_scope() as session:
        batches = await fetch_batches(session, date_from=date_from, date_to=date_to)
        unknown = await fetch_unknown_phones(session, [row.id for row in batches])
    text = build_report(
        batches,
        title="Ежедневная аналитика",
        date_from=date_from,
        date_to=date_to,
        timezone=settings.timezone,
        unknown_phones=unknown,
    )
    await context.bot.send_message(chat_id=settings.admin_chat_id, text=text)
