"""Aggregation logic behind the Overview dashboard."""
import calendar
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.dashboard import (
    CategoryBreakdownChildItem,
    CategoryBreakdownItem,
    CurrencyDashboardSummary,
    DashboardSummary,
)
from app.services.category_rollup import rollup_spending_by_top_level_category

# Categorical slots are capped at 8 (dataviz skill: a 9th series folds into "Other",
# never a generated hue) — this is also the exact size of the default category set.
MAX_CHART_SLICES = 8
OTHER_SLICE_COLOR = "#898781"  # muted ink, reserved for the non-categorical rollup


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


async def _totals_for_scope(
    session: AsyncSession,
    start: date,
    end: date,
    currency: str | None = None,
) -> dict[TransactionType, Decimal]:
    stmt = (
        select(Transaction.type, func.coalesce(func.sum(Transaction.amount), 0))
        .join(Account, Account.id == Transaction.account_id)
        .where(Transaction.date >= start, Transaction.date <= end)
        .group_by(Transaction.type)
    )
    if currency is not None:
        stmt = stmt.where(Account.currency == currency)
    result = await session.execute(stmt)
    return {row[0]: row[1] for row in result.all()}


async def _currencies_in_month(session: AsyncSession, start: date, end: date) -> list[str]:
    stmt = (
        select(Account.currency)
        .join(Transaction, Transaction.account_id == Account.id)
        .where(Transaction.date >= start, Transaction.date <= end)
        .distinct()
        .order_by(Account.currency)
    )
    return list((await session.execute(stmt)).scalars().all())


def _category_breakdown(
    rows,
    spent: Decimal,
) -> list[CategoryBreakdownItem]:
    top_rows, rest_rows = rows[:MAX_CHART_SLICES], rows[MAX_CHART_SLICES:]

    def _percent(amount: Decimal) -> float:
        return float(amount / spent * 100) if spent else 0.0

    spending_by_category = [
        CategoryBreakdownItem(
            category_id=row.category_id,
            name=row.name,
            color=row.color,
            icon=row.icon,
            amount=row.amount,
            percent=_percent(row.amount),
            children=[
                CategoryBreakdownChildItem(
                    category_id=child.category_id,
                    name=child.name,
                    color=child.color,
                    icon=child.icon,
                    amount=child.amount,
                )
                for child in row.children
            ],
        )
        for row in top_rows
    ]

    if rest_rows:
        other_amount = sum((row.amount for row in rest_rows), Decimal("0"))
        spending_by_category.append(
            CategoryBreakdownItem(
                category_id=None,
                name="Other",
                color=OTHER_SLICE_COLOR,
                icon="more-horizontal",
                amount=other_amount,
                percent=_percent(other_amount),
            )
        )
    return spending_by_category


async def _currency_summary(
    session: AsyncSession,
    start: date,
    end: date,
    currency: str,
) -> CurrencyDashboardSummary:
    totals = await _totals_for_scope(session, start, end, currency=currency)
    real_income = totals.get(TransactionType.INCOME, Decimal("0"))
    spent = totals.get(TransactionType.EXPENSE, Decimal("0"))
    transferred_out = totals.get(TransactionType.TRANSFER, Decimal("0"))
    rows = await rollup_spending_by_top_level_category(
        session,
        transaction_type=TransactionType.EXPENSE,
        start_date=start,
        end_date=end,
        currency=currency,
    )
    return CurrencyDashboardSummary(
        currency=currency,
        real_income=real_income,
        spent=spent,
        net=real_income - spent,
        transferred_out=transferred_out,
        spending_by_category=_category_breakdown(rows, spent),
    )


async def get_dashboard_summary(session: AsyncSession, year: int, month: int) -> DashboardSummary:
    start, end = _month_bounds(year, month)

    # Legacy mixed totals — kept for advice/insights and older clients.
    mixed_totals = await _totals_for_scope(session, start, end, currency=None)
    real_income = mixed_totals.get(TransactionType.INCOME, Decimal("0"))
    spent = mixed_totals.get(TransactionType.EXPENSE, Decimal("0"))
    transferred_out = mixed_totals.get(TransactionType.TRANSFER, Decimal("0"))
    mixed_rows = await rollup_spending_by_top_level_category(
        session,
        transaction_type=TransactionType.EXPENSE,
        start_date=start,
        end_date=end,
        currency=None,
    )

    currencies = await _currencies_in_month(session, start, end)
    by_currency = [await _currency_summary(session, start, end, code) for code in currencies]

    return DashboardSummary(
        year=year,
        month=month,
        real_income=real_income,
        spent=spent,
        net=real_income - spent,
        transferred_out=transferred_out,
        spending_by_category=_category_breakdown(mixed_rows, spent),
        by_currency=by_currency,
    )
