"""suite_steps replace setup/teardown text

Revision ID: d1e3f5a7b9c2
Revises: c4f8a2b1d7e9
Create Date: 2026-05-03

"""
from alembic import op
import sqlalchemy as sa

revision = 'd1e3f5a7b9c2'
down_revision = 'c4f8a2b1d7e9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'suite_steps',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('suite_id', sa.Integer, sa.ForeignKey('test_suites.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order', sa.Integer, nullable=False),
        sa.Column('step_type', sa.String(16), nullable=False),
        sa.Column('action', sa.Text, nullable=False),
    )
    op.drop_column('test_suites', 'setup')
    op.drop_column('test_suites', 'teardown')


def downgrade() -> None:
    op.add_column('test_suites', sa.Column('setup', sa.Text, nullable=True))
    op.add_column('test_suites', sa.Column('teardown', sa.Text, nullable=True))
    op.drop_table('suite_steps')
