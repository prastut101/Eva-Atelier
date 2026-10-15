"""Add image_url to products.

Revision ID: 55894ce6f3fc
Revises: 4f37eee2c996
"""

from alembic import op
import sqlalchemy as sa

revision = "55894ce6f3fc"
down_revision = "4f37eee2c996"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("image_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("products", "image_url")
