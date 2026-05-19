"""public_reports

Revision ID: c7d8e9f0a1b2
Revises: 68c5c4c30227, a1b2c3d4e5f6, a4b7c2d9e1f6
Create Date: 2026-05-20 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import testjam.models._types

revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = (
    "68c5c4c30227",
    "a1b2c3d4e5f6",
    "a4b7c2d9e1f6",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "public_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=True),
        sa.Column("execution_id", sa.Integer(), nullable=True),
        sa.Column("version_id", sa.Integer(), nullable=True),
        sa.Column("environment", sa.String(length=64), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            testjam.models._types.UTCDateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            testjam.models._types.UTCDateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "revoked_at",
            testjam.models._types.UTCDateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_viewed_at",
            testjam.models._types.UTCDateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "view_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["execution_id"], ["test_executions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["version_id"], ["project_versions.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("token_hash", name="uq_public_reports_token_hash"),
    )
    op.create_index(
        "ix_public_reports_project_id", "public_reports", ["project_id"]
    )
    op.create_index(
        "ix_public_reports_token_hash", "public_reports", ["token_hash"]
    )
    op.create_index(
        "ix_public_reports_execution_id", "public_reports", ["execution_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_public_reports_execution_id", table_name="public_reports")
    op.drop_index("ix_public_reports_token_hash", table_name="public_reports")
    op.drop_index("ix_public_reports_project_id", table_name="public_reports")
    op.drop_table("public_reports")
