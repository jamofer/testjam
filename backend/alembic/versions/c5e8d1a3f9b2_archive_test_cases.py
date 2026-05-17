"""add archived_at to test_cases

Revision ID: c5e8d1a3f9b2
Revises: b4f7d2c8e9a1
Create Date: 2026-05-17 21:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c5e8d1a3f9b2"
down_revision: Union[str, None] = "b4f7d2c8e9a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "test_cases",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("test_cases", "archived_at")
