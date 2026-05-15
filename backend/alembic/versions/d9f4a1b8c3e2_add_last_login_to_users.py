"""add last_login_at and last_login_ip to users

Revision ID: d9f4a1b8c3e2
Revises: 7b2bdd216691
Create Date: 2026-05-15 18:05:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d9f4a1b8c3e2"
down_revision: Union[str, None] = "7b2bdd216691"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_login_ip", sa.String(length=45), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_login_ip")
    op.drop_column("users", "last_login_at")
