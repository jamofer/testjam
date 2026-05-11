"""add started_at to test_step_results

Revision ID: c5a2b8e4d6f1
Revises: b8e4d2c6f1a9
Create Date: 2026-05-11 19:10:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c5a2b8e4d6f1"
down_revision: Union[str, None] = "b8e4d2c6f1a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "test_step_results",
        sa.Column("started_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("test_step_results", "started_at")
