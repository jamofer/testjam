"""cascade delete parent suite

Revision ID: e6a3c19f4d72
Revises: d2b1c8f5a3e7
Create Date: 2026-05-18 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op


revision: str = 'e6a3c19f4d72'
down_revision: Union[str, None] = 'd2b1c8f5a3e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FK_NAME = "test_suites_parent_suite_id_fkey"


def upgrade() -> None:
    op.drop_constraint(FK_NAME, "test_suites", type_="foreignkey")
    op.create_foreign_key(
        FK_NAME,
        "test_suites",
        "test_suites",
        ["parent_suite_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(FK_NAME, "test_suites", type_="foreignkey")
    op.create_foreign_key(
        FK_NAME,
        "test_suites",
        "test_suites",
        ["parent_suite_id"],
        ["id"],
        ondelete="SET NULL",
    )
