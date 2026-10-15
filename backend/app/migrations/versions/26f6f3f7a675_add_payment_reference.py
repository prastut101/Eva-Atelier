"""add payment reference

Revision ID: 26f6f3f7a675
Revises: 4a2aa452460a
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "26f6f3f7a675"
down_revision: Union[str, Sequence[str], None] = "4a2aa452460a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("payment_reference", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_orders_payment_reference",
        "orders",
        ["payment_reference"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_orders_payment_reference", table_name="orders")
    op.drop_column("orders", "payment_reference")
