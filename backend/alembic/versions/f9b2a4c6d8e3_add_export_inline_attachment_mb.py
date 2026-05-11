"""add export_inline_attachment_mb to app_settings

Revision ID: f9b2a4c6d8e3
Revises: e8f1c2a3b9d4
Create Date: 2026-05-12 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f9b2a4c6d8e3'
down_revision: Union[str, None] = 'e8f1c2a3b9d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column(
            "export_inline_attachment_mb",
            sa.Integer(),
            nullable=False,
            server_default="10",
        ),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "export_inline_attachment_mb")
