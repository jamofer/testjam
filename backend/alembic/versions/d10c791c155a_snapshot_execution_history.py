"""snapshot case and step text on execution results

Revision ID: d10c791c155a
Revises: 0799fc4d990b
Create Date: 2026-10-26 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'd10c791c155a'
down_revision: Union[str, None] = '0799fc4d990b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RESULT_CASE_FK = "test_results_test_case_id_fkey"
STEP_RESULT_STEP_FK = "test_step_results_step_id_fkey"


def upgrade() -> None:
    op.add_column("test_results", sa.Column("test_case_title", sa.String(length=255), nullable=True))
    op.add_column("test_step_results", sa.Column("step_action", sa.Text(), nullable=True))
    op.add_column("test_step_results", sa.Column("step_expected_result", sa.Text(), nullable=True))
    op.execute("""
        UPDATE test_results r
        SET test_case_title = c.name
        FROM test_cases c
        WHERE c.id = r.test_case_id
    """)
    op.execute("""
        UPDATE test_step_results sr
        SET step_action = s.action, step_expected_result = s.expected_result
        FROM test_steps s
        WHERE s.id = sr.step_id
    """)
    _replace_foreign_key(RESULT_CASE_FK, "test_results", "test_cases", "test_case_id", "SET NULL")
    _replace_foreign_key(STEP_RESULT_STEP_FK, "test_step_results", "test_steps", "step_id", "SET NULL")
    op.alter_column("test_results", "test_case_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("test_step_results", "step_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM test_step_results WHERE step_id IS NULL")
    op.execute("DELETE FROM test_results WHERE test_case_id IS NULL")
    op.alter_column("test_step_results", "step_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("test_results", "test_case_id", existing_type=sa.Integer(), nullable=False)
    _replace_foreign_key(STEP_RESULT_STEP_FK, "test_step_results", "test_steps", "step_id", "CASCADE")
    _replace_foreign_key(RESULT_CASE_FK, "test_results", "test_cases", "test_case_id", "CASCADE")
    op.drop_column("test_step_results", "step_expected_result")
    op.drop_column("test_step_results", "step_action")
    op.drop_column("test_results", "test_case_title")


def _replace_foreign_key(name: str, table: str, referred_table: str, column: str, ondelete: str) -> None:
    op.drop_constraint(name, table, type_="foreignkey")
    op.create_foreign_key(name, table, referred_table, [column], ["id"], ondelete=ondelete)
