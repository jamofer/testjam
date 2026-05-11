"""add user notification preferences

Revision ID: a7f3c8b9e2d1
Revises: 461099e5bde1
Create Date: 2026-05-11 18:40:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a7f3c8b9e2d1"
down_revision: Union[str, None] = "461099e5bde1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_notification_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("in_app", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("email", sa.Boolean(), server_default="false", nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "event_type",
            name="uq_user_notification_preferences_user_event",
        ),
    )
    op.create_index(
        op.f("ix_user_notification_preferences_user_id"),
        "user_notification_preferences",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_user_notification_preferences_user_id"),
        table_name="user_notification_preferences",
    )
    op.drop_table("user_notification_preferences")
