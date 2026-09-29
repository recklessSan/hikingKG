from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Привет! Я бот Aurum — записываю расходы в вашу базу.\n\n"
        "Команды:\n"
        "/expense — добавить расход (пошагово)\n"
        "/cancel — отменить текущий диалог\n"
        "/id — показать ваш Telegram user id"
    )


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(f"Ваш Telegram user id: `{message.from_user.id}`", parse_mode="Markdown")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено. /expense — начать заново.")
