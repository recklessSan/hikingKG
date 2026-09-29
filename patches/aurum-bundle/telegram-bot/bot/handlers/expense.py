from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.api import AurumApiError, AurumClient
from bot.keyboards import accounts_keyboard, categories_keyboard, confirm_keyboard
from bot.states import ExpenseFlow

router = Router()


def _parse_amount(text: str) -> Decimal | None:
    cleaned = text.strip().replace(" ", "").replace(",", ".")
    try:
        amount = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None
    if amount <= 0:
        return None
    return amount.quantize(Decimal("0.01"))


async def _start_expense(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ExpenseFlow.amount)
    await message.answer(
        "Шаг 1/4 — сумма расхода\n"
        "Напишите число, например: `150.50`",
        parse_mode="Markdown",
    )


@router.message(Command("expense"))
async def cmd_expense(message: Message, state: FSMContext) -> None:
    await _start_expense(message, state)


@router.message(F.text.regexp(r"(?i)^расход$"))
async def text_expense(message: Message, state: FSMContext) -> None:
    await _start_expense(message, state)


@router.message(ExpenseFlow.amount)
async def step_amount(message: Message, state: FSMContext) -> None:
    amount = _parse_amount(message.text or "")
    if amount is None:
        await message.answer("Не понял сумму. Пример: `200` или `45.90`", parse_mode="Markdown")
        return
    await state.update_data(amount=str(amount))
    await state.set_state(ExpenseFlow.description)
    await message.answer("Шаг 2/4 — описание\nНапишите коротко, на что потратили (например: продукты).")


@router.message(ExpenseFlow.description)
async def step_description(message: Message, state: FSMContext, api: AurumClient) -> None:
    description = (message.text or "").strip()
    if len(description) < 1:
        await message.answer("Описание не может быть пустым. Напишите ещё раз.")
        return
    if len(description) > 255:
        await message.answer("Слишком длинно (макс. 255 символов). Сократите.")
        return

    await state.update_data(description=description)
    try:
        accounts = await api.list_accounts()
    except AurumApiError as exc:
        await state.clear()
        await message.answer(f"Не удалось загрузить счета: {exc}")
        return

    if not accounts:
        await state.clear()
        await message.answer("В Aurum нет счетов. Создайте счёт в приложении и повторите.")
        return

    await state.set_state(ExpenseFlow.account)
    await message.answer("Шаг 3/4 — счёт", reply_markup=accounts_keyboard(accounts))


@router.callback_query(ExpenseFlow.account, F.data.startswith("acc:"))
async def step_account(callback: CallbackQuery, state: FSMContext, api: AurumClient) -> None:
    account_id = int(callback.data.split(":", 1)[1])
    try:
        accounts = await api.list_accounts()
        categories = await api.list_expense_categories()
    except AurumApiError as exc:
        await state.clear()
        await callback.message.answer(f"Ошибка API: {exc}")
        await callback.answer()
        return

    account = next((row for row in accounts if row["id"] == account_id), None)
    if account is None:
        await callback.answer("Счёт не найден", show_alert=True)
        return

    await state.update_data(
        account_id=account_id,
        account_name=account["name"],
        account_currency=account["currency"],
    )

    if not categories:
        await state.clear()
        await callback.message.edit_text("Нет категорий расходов. Добавьте их в Aurum.")
        await callback.answer()
        return

    await state.set_state(ExpenseFlow.category)
    await callback.message.edit_text(
        f"Счёт: {account['name']} ({account['currency']})\n\nШаг 4/4 — категория",
        reply_markup=categories_keyboard(categories),
    )
    await callback.answer()


@router.callback_query(ExpenseFlow.category, F.data.startswith("cat:"))
async def step_category(callback: CallbackQuery, state: FSMContext, api: AurumClient) -> None:
    category_id = int(callback.data.split(":", 1)[1])
    try:
        categories = await api.list_expense_categories()
    except AurumApiError as exc:
        await state.clear()
        await callback.message.answer(f"Ошибка API: {exc}")
        await callback.answer()
        return

    category = next((row for row in categories if row["id"] == category_id), None)
    if category is None:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    await state.update_data(category_id=category_id, category_name=category["name"])
    data = await state.get_data()
    await state.set_state(ExpenseFlow.confirm)
    await callback.message.edit_text(
        "Проверьте расход:\n\n"
        f"• Сумма: {data['amount']} {data['account_currency']}\n"
        f"• Описание: {data['description']}\n"
        f"• Счёт: {data['account_name']}\n"
        f"• Категория: {data['category_name']}\n\n"
        "Сохранить в Aurum?",
        reply_markup=confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(ExpenseFlow.confirm, F.data == "confirm:yes")
async def step_confirm(callback: CallbackQuery, state: FSMContext, api: AurumClient) -> None:
    data = await state.get_data()
    try:
        created = await api.create_expense(
            account_id=int(data["account_id"]),
            category_id=int(data["category_id"]),
            amount=Decimal(data["amount"]),
            description=data["description"],
        )
    except AurumApiError as exc:
        await callback.message.edit_text(f"Не удалось сохранить: {exc}")
        await state.clear()
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_text(
        f"Готово. Расход #{created.get('id')} записан:\n"
        f"{data['amount']} {data['account_currency']} — {data['description']}\n"
        f"{data['account_name']} · {data['category_name']}\n\n"
        "/expense — ещё один"
    )
    await callback.answer("Сохранено")


@router.callback_query(F.data == "cancel")
async def step_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_text("Отменено. /expense — начать заново.")
    await callback.answer()
