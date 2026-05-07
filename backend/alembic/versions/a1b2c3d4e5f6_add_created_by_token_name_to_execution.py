"""add created_by_id and token_name to test_executions

Revision ID: a1b2c3d4e5f6
Revises: f3a1d8c5e2b4
Create Date: 2026-05-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "f3a1d8c5e2b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_executions",
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "test_executions",
        sa.Column("token_name", sa.String(128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("test_executions", "token_name")
    op.drop_column("test_executions", "created_by_id")
