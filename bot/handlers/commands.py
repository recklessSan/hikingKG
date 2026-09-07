from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import Settings
from bot.db.models import PhoneDirectory
from bot.db.session import session_scope
from bot.parsers.phones import format_phone, normalize_phone
from bot.services.ingest import fetch_batches
from bot.services.phones import fetch_unknown_phones, import_phones_csv, lookup_directory, upsert_directory_phone
from bot.services.reports import build_report, format_check_result, period_for_today, period_for_week

HELP_TEXT = """Бот считает аналитику партий и проверяет телефоны из чата 1 по справочнику.

Команды:
/today — отчёт за сегодня
/week — отчёт за 7 дней
/stats — все сохранённые данные
/toffice — только «передано в Т-офис»
/report 07.09.2026 — день
/report 01.09.2026 07.09.2026 — период
/phones — проверка телефонов за сегодня
/check 79001234567 — найти номер в справочнике
/phones_add 79001234567 метка — добавить номер в справочник
/phones_reload — загрузить CSV из PHONES_FILE
/chatid — id текущего чата
/help — эта справка

В админ-чат можно прислать CSV со столбцами phone,label.

Чат 1: банк, количество, телефоны (проверка по базе), автор, дата.
Чат 2: только блок «ПЕРЕДАНО В Т-ОФИС».
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


async def cmd_phones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_report(update, context, period="today", title="Проверка телефонов")


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


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not is_admin(update, settings) or not update.effective_message:
        return
    raw = " ".join(context.args or []).strip()
    phone = normalize_phone(raw)
    if phone is None:
        await update.effective_message.reply_text("Пришлите телефон: /check +7 900 123-45-67")
        return
    async with session_scope() as session:
        row = await lookup_directory(session, phone)
    await update.effective_message.reply_text(
        format_check_result(phone, row.label if row else None, row is not None)
    )


async def cmd_phones_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not is_admin(update, settings) or not update.effective_message:
        return
    args = list(context.args or [])
    if not args:
        await update.effective_message.reply_text("Формат: /phones_add +7 900 123-45-67 метка")
        return
    phone = None
    label = None
    for end in range(1, len(args) + 1):
        candidate = normalize_phone(" ".join(args[:end]))
        if candidate:
            phone = candidate
            label = " ".join(args[end:]).strip() or None
            break
    if phone is None:
        await update.effective_message.reply_text("Не похоже на телефон. Пример: /phones_add 79001234567 склад")
        return
    async with session_scope() as session:
        row = await upsert_directory_phone(session, phone, label=label, source="manual")
    if row is None:
        await update.effective_message.reply_text("Номер не сохранён")
        return
    await update.effective_message.reply_text(f"добавлен {format_phone(row.phone)}" + (f" ({row.label})" if row.label else ""))


async def cmd_phones_reload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not is_admin(update, settings) or not update.effective_message:
        return
    path = Path(settings.phones_file)
    if not path.is_file():
        await update.effective_message.reply_text(f"файл не найден: {path}")
        return
    async with session_scope() as session:
        imported = await import_phones_csv(session, path)
        total = await session.scalar(select(func.count()).select_from(PhoneDirectory)) or 0
    await update.effective_message.reply_text(f"загружено из CSV: {imported}\nвсего в справочнике: {total}")


async def _reply_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    period: str,
    event_type: str | None = None,
    title: str = "Аналитика",
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
        unknown = await fetch_unknown_phones(session, [row.id for row in batches])
    text = build_report(
        batches,
        title=title,
        date_from=date_from,
        date_to=date_to,
        timezone=settings.timezone,
        unknown_phones=unknown,
    )
    await update.effective_message.reply_text(text)
