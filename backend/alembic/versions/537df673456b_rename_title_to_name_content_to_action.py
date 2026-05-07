"""rename title to name, content to action

Revision ID: 537df673456b
Revises: c8b52cb822a5
Create Date: 2026-05-03 16:32:27.063595
"""
from typing import Sequence, Union
from alembic import op


revision: str = '537df673456b'
down_revision: Union[str, None] = 'c8b52cb822a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('test_suites', 'title', new_column_name='name')
    op.alter_column('test_cases', 'title', new_column_name='name')
    op.alter_column('test_steps', 'content', new_column_name='action')


def downgrade() -> None:
    op.alter_column('test_suites', 'name', new_column_name='title')
    op.alter_column('test_cases', 'name', new_column_name='title')
    op.alter_column('test_steps', 'action', new_column_name='content')
