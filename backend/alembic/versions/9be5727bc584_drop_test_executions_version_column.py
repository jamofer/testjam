"""drop test_executions.version column

Revision ID: 9be5727bc584
Revises: 7a61b8d489ef
Create Date: 2026-05-16 21:48:59.139399
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = '9be5727bc584'
down_revision: Union[str, None] = '7a61b8d489ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        INSERT INTO project_versions (project_id, name, status, created_at)
        SELECT DISTINCT te.project_id, te.version, 'active', NOW()
        FROM test_executions te
        WHERE te.version IS NOT NULL
          AND te.version <> ''
          AND te.version_id IS NULL
          AND NOT EXISTS (
            SELECT 1 FROM project_versions pv
            WHERE pv.project_id = te.project_id
              AND LOWER(pv.name) = LOWER(te.version)
          )
    """))
    conn.execute(text("""
        UPDATE test_executions te
        SET version_id = pv.id
        FROM project_versions pv
        WHERE te.version_id IS NULL
          AND te.version IS NOT NULL
          AND te.version <> ''
          AND pv.project_id = te.project_id
          AND LOWER(pv.name) = LOWER(te.version)
    """))
    op.drop_column('test_executions', 'version')


def downgrade() -> None:
    op.add_column('test_executions', sa.Column('version', sa.String(length=64), nullable=True))
