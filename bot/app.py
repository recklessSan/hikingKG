from __future__ import annotations

import logging
from datetime import time
from zoneinfo import ZoneInfo

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.config import Settings
from bot.db.session import create_tables, init_engine
from bot.handlers.commands import (
    cmd_chatid,
    cmd_help,
    cmd_report,
    cmd_start,
    cmd_stats,
    cmd_today,
    cmd_toffice,
    cmd_week,
)
from bot.handlers.messages import on_text_message
from bot.scheduler import send_daily_report

logger = logging.getLogger(__name__)


def build_application(settings: Settings) -> Application:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set")

    init_engine(settings)

    application = (
        Application.builder()
        .token(settings.bot_token)
        .post_init(_post_init)
        .build()
    )
    application.bot_data["settings"] = settings

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("chatid", cmd_chatid))
    application.add_handler(CommandHandler("today", cmd_today))
    application.add_handler(CommandHandler("week", cmd_week))
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("toffice", cmd_toffice))
    application.add_handler(CommandHandler("report", cmd_report))
    text_filter = filters.TEXT & ~filters.COMMAND
    application.add_handler(MessageHandler(text_filter, on_text_message))
    application.add_handler(
        MessageHandler(filters.UpdateType.EDITED_MESSAGE & filters.TEXT, on_text_message)
    )
    application.add_handler(
        MessageHandler(filters.UpdateType.CHANNEL_POST & filters.TEXT, on_text_message)
    )
    application.add_handler(
        MessageHandler(filters.UpdateType.EDITED_CHANNEL_POST & filters.TEXT, on_text_message)
    )

    tz = ZoneInfo(settings.timezone)
    application.job_queue.run_daily(
        send_daily_report,
        time=time(hour=settings.report_hour, minute=settings.report_minute, tzinfo=tz),
        name="daily_card_report",
    )
    return application


async def _post_init(application: Application) -> None:
    await create_tables()
    logger.info("database is ready")
