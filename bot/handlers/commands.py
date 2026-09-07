from __future__ import annotations

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import Settings
from bot.db.session import session_scope
from bot.services.ingest import fetch_batches
from bot.services.reports import build_report, period_for_today, period_for_week

HELP_TEXT = """Бот считает аналитику по картам без хранения номеров.

Команды:
/today — отчёт за сегодня
/week — отчёт за 7 дней
/stats — все сохранённые данные
/toffice — только «передано в Т-офис»
/report 07.09.2026 — день
/report 01.09.2026 07.09.2026 — период
/chatid — id текущего чата
/help — эта справка

В чатах-источниках бот молча разбирает сообщения:
1) банк, количество, кэш/без ЛК, автор, дата
2) только блок «ПЕРЕДАНО В Т-ОФИС»
3) формат как у чата 1 или 2 (CHAT_3_MODE)
"""


def is_admin(update: Update, settings: Settings) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if user and user.id in settings.admin_user_ids:
        return True
    if chat and settings.admin_chat_id is not None and chat.id == settings.admin_chat_id:
        return True
    return False


async def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not update.effective_message or chat is None:
        return
    await update.effective_message.reply_text(f"chat id: {chat.id}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return
    await update.effective_message.reply_text(HELP_TEXT)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_report(update, context, period="today")


async def cmd_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_report(update, context, period="week")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_report(update, context, period="all")


async def cmd_toffice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_report(update, context, period="all", event_type="t_office", title="Т-офис")


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not is_admin(update, settings) or not update.effective_message:
        return
    args = context.args or []
    if not args:
        await update.effective_message.reply_text("Формат: /report 07.09.2026 или /report 01.09.2026 07.09.2026")
        return
    try:
        date_from = datetime.strptime(args[0], "%d.%m.%Y").date()
        date_to = datetime.strptime(args[1], "%d.%m.%Y").date() if len(args) > 1 else date_from
    except ValueError:
        await update.effective_message.reply_text("Дата должна быть в формате ДД.ММ.ГГГГ")
        return
    await _send_report(update, settings, date_from, date_to, title="Отчёт")


async def _reply_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    period: str,
    event_type: str | None = None,
    title: str = "Аналитика карт",
) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not is_admin(update, settings) or not update.effective_message:
        return
    if period == "today":
        date_from, date_to = period_for_today(settings.timezone)
    elif period == "week":
        date_from, date_to = period_for_week(settings.timezone)
    else:
        date_from, date_to = None, None
    await _send_report(
        update,
        settings,
        date_from,
        date_to,
        title=title,
        event_type=event_type,
    )


async def _send_report(
    update: Update,
    settings: Settings,
    date_from,
    date_to,
    *,
    title: str,
    event_type: str | None = None,
) -> None:
    async with session_scope() as session:
        batches = await fetch_batches(
            session,
            date_from=date_from,
            date_to=date_to,
            event_type=event_type,
        )
    text = build_report(
        batches,
        title=title,
        date_from=date_from,
        date_to=date_to,
        timezone=settings.timezone,
    )
    await update.effective_message.reply_text(text)
