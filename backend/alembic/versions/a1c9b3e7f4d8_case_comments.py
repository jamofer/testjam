"""add case_comments table

Revision ID: a1c9b3e7f4d8
Revises: f5a8d2c1e9b7
Create Date: 2026-05-17 17:20:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a1c9b3e7f4d8"
down_revision: Union[str, None] = "f5a8d2c1e9b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "test_case_id", sa.Integer(),
            sa.ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_by_id", sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_case_comments_test_case_id", "case_comments", ["test_case_id"])


def downgrade() -> None:
    op.drop_index("ix_case_comments_test_case_id", table_name="case_comments")
    op.drop_table("case_comments")
