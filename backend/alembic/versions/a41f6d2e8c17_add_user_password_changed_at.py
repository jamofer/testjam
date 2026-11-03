"""add user password_changed_at

Revision ID: a41f6d2e8c17
Revises: 7c2e4f1a9b30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a41f6d2e8c17'
down_revision: Union[str, None] = '7c2e4f1a9b30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_changed_at')
