"""add is_primary flag to accounts

Revision ID: e4b2c9a17f30
Revises: d1a6f4c8b729
Create Date: 2026-09-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e4b2c9a17f30"
down_revision: Union[str, None] = "d1a6f4c8b729"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # At most one primary account at a time.
    op.create_index(
        "ix_accounts_one_primary",
        "accounts",
        ["is_primary"],
        unique=True,
        postgresql_where=sa.text("is_primary IS TRUE"),
    )


def downgrade() -> None:
    op.drop_index("ix_accounts_one_primary", table_name="accounts")
    op.drop_column("accounts", "is_primary")
