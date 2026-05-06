"""merge heads

Revision ID: b46b23df19fd
Revises: a1b2c3d4e5f6, a4b7c2d9e1f6
Create Date: 2026-05-06 23:22:50.377931
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b46b23df19fd'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', 'a4b7c2d9e1f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
