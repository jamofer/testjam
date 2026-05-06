"""add order to test_suites and test_cases

Revision ID: ad2d55a50ae5
Revises: b46b23df19fd
Create Date: 2026-05-06 23:22:54.962825
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'ad2d55a50ae5'
down_revision: Union[str, None] = 'b46b23df19fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('test_suites', sa.Column('order', sa.Integer(), server_default='0', nullable=False))
    op.add_column('test_cases',  sa.Column('order', sa.Integer(), server_default='0', nullable=False))

    # Backfill: sequential order per (project_id, parent_suite_id) for suites,
    # and per suite_id for cases — using id ascending so existing layout is preserved.
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        bind.execute(sa.text("""
            UPDATE test_suites s SET "order" = sub.rn
            FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY project_id, COALESCE(parent_suite_id, 0)
                    ORDER BY id
                ) AS rn
                FROM test_suites
            ) sub
            WHERE s.id = sub.id
        """))
        bind.execute(sa.text("""
            UPDATE test_cases c SET "order" = sub.rn
            FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY suite_id ORDER BY id
                ) AS rn
                FROM test_cases
            ) sub
            WHERE c.id = sub.id
        """))


def downgrade() -> None:
    op.drop_column('test_cases', 'order')
    op.drop_column('test_suites', 'order')
