"""add duration_ms to test_step_results

Revision ID: f3a1d8c5e2b4
Revises: e2a9c4f1b8d3
Create Date: 2026-05-04

"""
import sqlalchemy as sa

from alembic import op

revision = 'f3a1d8c5e2b4'
down_revision = 'e2a9c4f1b8d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('test_step_results', sa.Column('duration_ms', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('test_step_results', 'duration_ms')
