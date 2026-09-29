from decimal import Decimal

from pydantic import BaseModel, Field


class CategoryBreakdownChildItem(BaseModel):
    """One subcategory's (or the parent's own direct, un-subcategorized)
    share of a CategoryBreakdownItem's total — see
    services/category_rollup.py's CategoryRollupChildItem."""

    category_id: int
    name: str
    color: str
    icon: str | None
    amount: Decimal


class CategoryBreakdownItem(BaseModel):
    category_id: int | None
    name: str
    color: str
    icon: str | None
    amount: Decimal
    percent: float
    # Populated only when this slice's spend came from more than one
    # distinct category (subcategories, or a mix of the parent itself and
    # its children) — e.g. a receipt split across "Groceries" subcategories.
    children: list[CategoryBreakdownChildItem] = Field(default_factory=list)


class CurrencyDashboardSummary(BaseModel):
    """One month's headline numbers for a single account currency.

    Amounts in different currencies are never mixed — each currency gets
    its own income/spent/net and its own spending-by-category donut.
    """

    currency: str
    real_income: Decimal
    spent: Decimal
    net: Decimal
    transferred_out: Decimal
    spending_by_category: list[CategoryBreakdownItem]


class DashboardSummary(BaseModel):
    year: int
    month: int
    # Legacy top-level totals (pre-multi-currency). Still populated for
    # advice/insights and older clients: when the month uses only one
    # currency they match that slice; with several currencies they stay
    # as the unconverted sum (historical behaviour) so callers that have
    # not moved to `by_currency` yet keep working. Prefer `by_currency`.
    real_income: Decimal
    spent: Decimal
    net: Decimal
    transferred_out: Decimal
    spending_by_category: list[CategoryBreakdownItem]
    by_currency: list[CurrencyDashboardSummary] = Field(default_factory=list)
