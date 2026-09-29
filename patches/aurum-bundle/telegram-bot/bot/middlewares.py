from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import get_settings


def _is_id_command(message: Message) -> bool:
    """Always allow /id so the user can learn their Telegram user id
    before (or after) filling AURUM_TELEGRAM_ALLOWED_USER_IDS."""
    text = (message.text or "").strip()
    if not text.startswith("/id"):
        return False
    # /id or /id@bot_username — nothing else
    cmd = text.split()[0]
    return cmd == "/id" or cmd.startswith("/id@")


class AllowlistMiddleware(BaseMiddleware):
    """Drop updates from anyone not listed in AURUM_TELEGRAM_ALLOWED_USER_IDS.

    Must be registered on message / callback_query routers (not dp.update):
    update-level middleware receives an Update, so isinstance(event, Message)
    never matches and replies were silently skipped.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return None

        if isinstance(event, Message) and _is_id_command(event):
            return await handler(event, data)

        allowed = get_settings().allowed_user_ids()

        if not allowed:
            text = (
                "Бот не настроен: задайте AURUM_TELEGRAM_ALLOWED_USER_IDS "
                f"(ваш Telegram user id) в .env и перезапустите telegram-bot.\n"
                f"Ваш id: {user.id}"
            )
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer("Нет доступа: задайте ALLOWED_USER_IDS", show_alert=True)
                if event.message:
                    await event.message.answer(text)
            return None

        if user.id not in allowed:
            text = f"Нет доступа. Ваш Telegram user id: {user.id}"
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer("Нет доступа.", show_alert=True)
                if event.message:
                    await event.message.answer(text)
            return None

        return await handler(event, data)
