from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.api import AurumClient
from bot.config import get_settings
from bot.handlers import setup_routers
from bot.middlewares import AllowlistMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("aurum-telegram-bot")


class InjectApiMiddleware(BaseMiddleware):
    def __init__(self, api: AurumClient) -> None:
        self.api = api

    async def __call__(self, handler, event, data):
        data["api"] = self.api
        return await handler(event, data)


async def _idle_without_token() -> None:
    log.warning(
        "AURUM_TELEGRAM_BOT_TOKEN is empty — bot idle. "
        "Set the token in .env and restart the telegram-bot container."
    )
    while True:
        await asyncio.sleep(3600)


async def main() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token.strip():
        await _idle_without_token()
        return

    api = AurumClient()
    for attempt in range(60):
        if await api.health():
            break
        log.info("Waiting for Aurum API at %s (%s/60)…", settings.telegram_api_base, attempt + 1)
        await asyncio.sleep(2)
    else:
        log.error("Aurum API did not become healthy; exiting so Docker can restart us.")
        await api.aclose()
        sys.exit(1)

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(AllowlistMiddleware())
    dp.update.middleware(InjectApiMiddleware(api))
    dp.include_router(setup_routers())

    log.info(
        "Aurum telegram bot starting (allowed users: %s)",
        sorted(settings.allowed_user_ids()) or "NONE — set AURUM_TELEGRAM_ALLOWED_USER_IDS",
    )
    try:
        await dp.start_polling(bot)
    finally:
        await api.aclose()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
