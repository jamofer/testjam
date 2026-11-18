"""add arguments to test_step_results

Revision ID: e7c3a9d1f5b2
Revises: b5d2e8f3c914
Create Date: 2026-11-18 12:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e7c3a9d1f5b2"
down_revision: str | None = "b5d2e8f3c914"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "test_step_results",
        sa.Column("arguments", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("test_step_results", "arguments")
