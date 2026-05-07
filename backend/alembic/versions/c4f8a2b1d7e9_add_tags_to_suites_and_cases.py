"""add tags to suites and cases

Revision ID: c4f8a2b1d7e9
Revises: b3e7f91a0d24
Create Date: 2026-05-03 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c4f8a2b1d7e9'
down_revision = 'b3e7f91a0d24'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('test_suites', sa.Column('tags', sa.JSON(), nullable=True))
    op.add_column('test_cases', sa.Column('tags', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('test_suites', 'tags')
    op.drop_column('test_cases', 'tags')
