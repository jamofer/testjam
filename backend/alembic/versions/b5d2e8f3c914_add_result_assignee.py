"""add test result assignee

Revision ID: b5d2e8f3c914
Revises: a41f6d2e8c17

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'b5d2e8f3c914'
down_revision: str | None = 'a41f6d2e8c17'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FOREIGN_KEY_NAME = 'fk_test_results_assigned_to_id_users'
INDEX_NAME = 'ix_test_results_assigned_to_id'


def upgrade() -> None:
    op.add_column('test_results', sa.Column('assigned_to_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        FOREIGN_KEY_NAME,
        'test_results', 'users',
        ['assigned_to_id'], ['id'], ondelete='SET NULL',
    )
    op.create_index(INDEX_NAME, 'test_results', ['assigned_to_id'], unique=False)


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name='test_results')
    op.drop_constraint(FOREIGN_KEY_NAME, 'test_results', type_='foreignkey')
    op.drop_column('test_results', 'assigned_to_id')
