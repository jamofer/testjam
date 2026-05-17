"""backfill bugs.updated_by_id = created_by_id for pre-existing rows

Revision ID: d8a3f1c5b7e9
Revises: d4c8b1f7a9e2
Create Date: 2026-05-17 12:10:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "d8a3f1c5b7e9"
down_revision: Union[str, None] = "d4c8b1f7a9e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE bugs SET updated_by_id = created_by_id "
        "WHERE updated_by_id IS NULL AND created_by_id IS NOT NULL"
    )


def downgrade() -> None:
    pass
