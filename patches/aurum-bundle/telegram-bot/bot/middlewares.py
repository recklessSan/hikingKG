from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import get_settings


class AllowlistMiddleware(BaseMiddleware):
    """Drop updates from anyone not listed in AURUM_TELEGRAM_ALLOWED_USER_IDS."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        allowed = get_settings().allowed_user_ids()
        if user is None:
            return None

        if not allowed:
            text = (
                "Бот не настроен: задайте AURUM_TELEGRAM_ALLOWED_USER_IDS "
                f"(ваш Telegram user id) в .env и перезапустите telegram-bot.\nВаш id: {user.id}"
            )
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer("Нет доступа: задайте ALLOWED_USER_IDS", show_alert=True)
                if event.message:
                    await event.message.answer(text)
            return None

        if user.id not in allowed:
            if isinstance(event, Message):
                await event.answer("Нет доступа.")
            elif isinstance(event, CallbackQuery):
                await event.answer("Нет доступа.", show_alert=True)
            return None

        return await handler(event, data)
