"""Add categories and nullable category_id to products.

Revision ID: 4f37eee2c996
Revises: 60881d5bcf0d
"""

from alembic import op
import sqlalchemy as sa

revision = "4f37eee2c996"
down_revision = "60881d5bcf0d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.UniqueConstraint("name", name="uq_categories_name"),
    )

    op.create_index(
        "ix_categories_id",
        "categories",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_categories_name",
        "categories",
        ["name"],
        unique=False,
    )

    with op.batch_alter_table("products") as batch_op:
        batch_op.add_column(
            sa.Column("category_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_products_category_id_categories",
            "categories",
            ["category_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_constraint(
            "fk_products_category_id_categories",
            type_="foreignkey",
        )
        batch_op.drop_column("category_id")

    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_index("ix_categories_id", table_name="categories")
    op.drop_table("categories")
