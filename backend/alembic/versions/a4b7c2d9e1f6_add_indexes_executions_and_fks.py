"""add indexes on test_executions.created_at and FK columns

Revision ID: a4b7c2d9e1f6
Revises: f3a1d8c5e2b4
Create Date: 2026-05-06

"""
from alembic import op

revision = 'a4b7c2d9e1f6'
down_revision = 'f3a1d8c5e2b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_test_executions_created_at', 'test_executions', ['created_at'])
    op.create_index('ix_test_results_execution_id', 'test_results', ['execution_id'])
    op.create_index('ix_test_cases_suite_id', 'test_cases', ['suite_id'])


def downgrade() -> None:
    op.drop_index('ix_test_cases_suite_id', table_name='test_cases')
    op.drop_index('ix_test_results_execution_id', table_name='test_results')
    op.drop_index('ix_test_executions_created_at', table_name='test_executions')
