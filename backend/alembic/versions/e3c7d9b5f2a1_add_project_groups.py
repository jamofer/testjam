"""add project_groups table

Revision ID: e3c7d9b5f2a1
Revises: d9f4a1b8c3e2
Create Date: 2026-05-15 18:40:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e3c7d9b5f2a1"
down_revision: Union[str, None] = "d9f4a1b8c3e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "group_id", name="uq_project_groups_project_group"),
    )
    op.create_index("ix_project_groups_project_id", "project_groups", ["project_id"])
    op.create_index("ix_project_groups_group_id", "project_groups", ["group_id"])
    op.execute("UPDATE groups SET description = '(unused)' WHERE description IS NULL")


def downgrade() -> None:
    op.drop_index("ix_project_groups_group_id", table_name="project_groups")
    op.drop_index("ix_project_groups_project_id", table_name="project_groups")
    op.drop_table("project_groups")
