from aiogram import Router

from bot.handlers import expense, start


def setup_routers() -> Router:
    root = Router()
    root.include_router(start.router)
    root.include_router(expense.router)
    return root
