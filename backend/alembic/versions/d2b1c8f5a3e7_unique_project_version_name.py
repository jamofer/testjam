"""unique project version name

Revision ID: d2b1c8f5a3e7
Revises: c5e8d1a3f9b2
Create Date: 2026-05-18 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op


revision: str = 'd2b1c8f5a3e7'
down_revision: Union[str, None] = 'c5e8d1a3f9b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE project_versions v
        SET name = v.name || ' #' || v.id
        FROM (
            SELECT project_id, name FROM project_versions
            GROUP BY project_id, name HAVING COUNT(*) > 1
        ) dup
        WHERE v.project_id = dup.project_id AND v.name = dup.name
          AND v.id NOT IN (
              SELECT MIN(id) FROM project_versions
              WHERE project_id = dup.project_id AND name = dup.name
          )
    """)
    op.create_unique_constraint(
        "uq_project_versions_project_name",
        "project_versions",
        ["project_id", "name"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_project_versions_project_name", "project_versions", type_="unique"
    )
