"""add bug_links.kind + bugs.fixed_in_version_id

Revision ID: e2b7d4a9f1c3
Revises: d8a3f1c5b7e9
Create Date: 2026-05-17 12:50:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e2b7d4a9f1c3"
down_revision: Union[str, None] = "d8a3f1c5b7e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bug_links",
        sa.Column("kind", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "bugs",
        sa.Column(
            "fixed_in_version_id",
            sa.Integer(),
            sa.ForeignKey("project_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("bugs", "fixed_in_version_id")
    op.drop_column("bug_links", "kind")
