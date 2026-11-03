"""drop plaintext user api key

Revision ID: 7c2e4f1a9b30
Revises: d10c791c155a

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '7c2e4f1a9b30'
down_revision: str | None = 'd10c791c155a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(op.f('ix_users_api_key'), table_name='users')
    op.drop_column('users', 'api_key')


def downgrade() -> None:
    op.add_column('users', sa.Column('api_key', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_users_api_key'), 'users', ['api_key'], unique=True)
