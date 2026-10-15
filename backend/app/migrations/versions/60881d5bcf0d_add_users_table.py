"""Add users table.

Revision ID: 60881d5bcf0d
Revises: 01a1ef70bec9
"""

from alembic import op
import sqlalchemy as sa

revision = "60881d5bcf0d"
down_revision = "01a1ef70bec9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Some existing databases already contain this table.
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "users" not in inspector.get_table_names():
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("username", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column(
                "is_admin",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
            sa.UniqueConstraint("username"),
        )
        op.create_index("ix_users_id", "users", ["id"])


def downgrade() -> None:
    # Preserve existing users and their credentials.
    pass
