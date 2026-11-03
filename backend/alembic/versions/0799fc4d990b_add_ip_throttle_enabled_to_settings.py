"""add_ip_throttle_enabled_to_settings

Revision ID: 0799fc4d990b
Revises: d3f7a8b2c1e9
Create Date: 2026-05-24 00:12:55.986521
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '0799fc4d990b'
down_revision: str | None = 'd3f7a8b2c1e9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column(
            "ip_throttle_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "ip_throttle_enabled")
