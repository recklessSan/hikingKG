"""Account CRUD, plus each account's live balance — summed from its
Transaction rows (income adds, expense subtracts, a transfer moves the
amount from the source account to the destination account) rather than
stored, the same "derive it, don't duplicate it" approach
net_worth_service.py uses for Cash.
"""
from collections import defaultdict
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.account import AccountCreate, AccountUpdate, AccountWithBalance


async def _account_balances(session: AsyncSession) -> dict[int, Decimal]:
    result = await session.execute(
        select(Transaction.type, Transaction.amount, Transaction.account_id, Transaction.transfer_account_id)
    )
    balances: dict[int, Decimal] = defaultdict(Decimal)
    for tx_type, amount, account_id, transfer_account_id in result.all():
        if tx_type == TransactionType.INCOME:
            balances[account_id] += amount
        elif tx_type == TransactionType.EXPENSE:
            balances[account_id] -= amount
        elif tx_type == TransactionType.TRANSFER:
            balances[account_id] -= amount
            if transfer_account_id is not None:
                balances[transfer_account_id] += amount
    return balances


def _to_read(account: Account, balance: Decimal) -> AccountWithBalance:
    return AccountWithBalance(
        id=account.id,
        name=account.name,
        type=account.type,
        currency=account.currency,
        color=account.color,
        is_archived=account.is_archived,
        is_primary=account.is_primary,
        balance=balance,
    )


async def _clear_other_primaries(session: AsyncSession, keep_account_id: int | None = None) -> None:
    """Ensure at most one account is primary. When keep_account_id is set,
    that row is left alone (caller is about to set / keep it primary)."""
    stmt = update(Account).where(Account.is_primary.is_(True)).values(is_primary=False)
    if keep_account_id is not None:
        stmt = stmt.where(Account.id != keep_account_id)
    await session.execute(stmt)


async def list_accounts(session: AsyncSession, include_archived: bool) -> list[AccountWithBalance]:
    # Primary first so expense/income/recurring forms (which default to
    # accounts[0]) land on the user's preferred account; then A→Z by name.
    stmt = select(Account).order_by(Account.is_primary.desc(), Account.name)
    if not include_archived:
        stmt = stmt.where(Account.is_archived.is_(False))
    accounts = (await session.execute(stmt)).scalars().all()
    balances = await _account_balances(session)
    return [_to_read(account, balances.get(account.id, Decimal("0"))) for account in accounts]


async def create_account(session: AsyncSession, payload: AccountCreate) -> AccountWithBalance:
    data = payload.model_dump()
    if data.get("is_primary"):
        await _clear_other_primaries(session)
    account = Account(**data)
    session.add(account)
    await session.commit()
    await session.refresh(account)
    # A brand-new account has no transactions yet — no need to query.
    return _to_read(account, Decimal("0"))


async def update_account(session: AsyncSession, account_id: int, payload: AccountUpdate) -> AccountWithBalance:
    account = await session.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    updates = payload.model_dump(exclude_unset=True)

    # Archiving the primary account drops the flag — an archived "default"
    # would otherwise stay sorted first while hidden from the picker.
    if updates.get("is_archived") is True:
        updates["is_primary"] = False

    if updates.get("is_primary") is True:
        await _clear_other_primaries(session, keep_account_id=account_id)

    for field, value in updates.items():
        setattr(account, field, value)

    await session.commit()
    await session.refresh(account)
    balances = await _account_balances(session)
    return _to_read(account, balances.get(account.id, Decimal("0")))


async def delete_account(session: AsyncSession, account_id: int) -> None:
    account = await session.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    await session.delete(account)
    await session.commit()
