"""add user password_changed_at

Revision ID: a41f6d2e8c17
Revises: 7c2e4f1a9b30

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'a41f6d2e8c17'
down_revision: str | None = '7c2e4f1a9b30'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_changed_at')
