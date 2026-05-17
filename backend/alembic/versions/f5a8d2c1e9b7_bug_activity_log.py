"""rename bug_status_history to bug_activity and generalize columns

Revision ID: f5a8d2c1e9b7
Revises: e2b7d4a9f1c3
Create Date: 2026-05-17 17:20:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f5a8d2c1e9b7"
down_revision: Union[str, None] = "e2b7d4a9f1c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("bug_status_history", "bug_activity")
    op.alter_column("bug_activity", "from_status", new_column_name="from_value", type_=sa.Text())
    op.alter_column("bug_activity", "to_status", new_column_name="to_value", type_=sa.Text(), existing_nullable=False, nullable=True)
    op.add_column("bug_activity", sa.Column("field", sa.String(length=32), nullable=True))
    op.execute("UPDATE bug_activity SET field = 'status' WHERE field IS NULL")
    op.alter_column("bug_activity", "field", existing_type=sa.String(length=32), nullable=False)
    op.create_index("ix_bug_activity_bug_id_changed_at", "bug_activity", ["bug_id", "changed_at"])


def downgrade() -> None:
    op.drop_index("ix_bug_activity_bug_id_changed_at", table_name="bug_activity")
    op.execute("DELETE FROM bug_activity WHERE field <> 'status'")
    op.drop_column("bug_activity", "field")
    op.alter_column("bug_activity", "to_value", new_column_name="to_status", type_=sa.String(length=16), nullable=False)
    op.alter_column("bug_activity", "from_value", new_column_name="from_status", type_=sa.String(length=16))
    op.rename_table("bug_activity", "bug_status_history")
