"""bug_watchers

Revision ID: 68c5c4c30227
Revises: a8c41f9e3b27
Create Date: 2026-05-19 21:36:52.320837
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import testjam.models._types

revision: str = '68c5c4c30227'
down_revision: Union[str, None] = 'a8c41f9e3b27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bug_watchers',
        sa.Column('bug_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            testjam.models._types.UTCDateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['bug_id'], ['bugs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('bug_id', 'user_id'),
    )


def downgrade() -> None:
    op.drop_table('bug_watchers')
