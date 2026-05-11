"""add smtp_reply_to to app_settings

Revision ID: b8e4d2c6f1a9
Revises: a7f3c8b9e2d1
Create Date: 2026-05-11 18:55:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b8e4d2c6f1a9"
down_revision: Union[str, None] = "a7f3c8b9e2d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column("smtp_reply_to", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "smtp_reply_to")
