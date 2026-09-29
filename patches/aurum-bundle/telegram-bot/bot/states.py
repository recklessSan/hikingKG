from aiogram.fsm.state import State, StatesGroup


class ExpenseFlow(StatesGroup):
    amount = State()
    description = State()
    account = State()
    category = State()
    confirm = State()
