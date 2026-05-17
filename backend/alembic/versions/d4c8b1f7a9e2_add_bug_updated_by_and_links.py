"""add bugs.updated_by_id + bug_links table

Revision ID: d4c8b1f7a9e2
Revises: c2e7f3a91b50
Create Date: 2026-05-17 11:40:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d4c8b1f7a9e2"
down_revision: Union[str, None] = "c2e7f3a91b50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bugs",
        sa.Column(
            "updated_by_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    op.create_table(
        "bug_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "bug_id",
            sa.Integer(),
            sa.ForeignKey("bugs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column(
            "execution_id",
            sa.Integer(),
            sa.ForeignKey("test_executions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "test_case_id",
            sa.Integer(),
            sa.ForeignKey("test_cases.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "test_step_id",
            sa.Integer(),
            sa.ForeignKey("test_steps.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_bug_id",
            sa.Integer(),
            sa.ForeignKey("bugs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("bug_links")
    op.drop_column("bugs", "updated_by_id")
