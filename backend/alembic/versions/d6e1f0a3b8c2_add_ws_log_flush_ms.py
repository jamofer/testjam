"""add ws_log_flush_ms to app_settings

Revision ID: d6e1f0a3b8c2
Revises: c5a2b8e4d6f1
Create Date: 2026-05-11 19:30:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d6e1f0a3b8c2"
down_revision: str | None = "c5a2b8e4d6f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column(
            "ws_log_flush_ms",
            sa.Integer(),
            nullable=False,
            server_default="100",
        ),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "ws_log_flush_ms")
