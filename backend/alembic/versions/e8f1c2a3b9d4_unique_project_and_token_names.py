"""unique project and token names

Revision ID: e8f1c2a3b9d4
Revises: d6e1f0a3b8c2
Create Date: 2026-05-12 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op


revision: str = 'e8f1c2a3b9d4'
down_revision: Union[str, None] = 'd6e1f0a3b8c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE projects p
        SET name = p.name || ' #' || p.id
        FROM (
            SELECT name FROM projects GROUP BY name HAVING COUNT(*) > 1
        ) dup
        WHERE p.name = dup.name
          AND p.id NOT IN (SELECT MIN(id) FROM projects WHERE name = dup.name)
    """)
    op.execute("""
        UPDATE api_tokens t
        SET name = t.name || ' #' || t.id
        FROM (
            SELECT user_id, name FROM api_tokens
            WHERE user_id IS NOT NULL
            GROUP BY user_id, name HAVING COUNT(*) > 1
        ) dup
        WHERE t.user_id = dup.user_id AND t.name = dup.name
          AND t.id NOT IN (
              SELECT MIN(id) FROM api_tokens WHERE user_id = dup.user_id AND name = dup.name
          )
    """)
    op.execute("""
        UPDATE api_tokens t
        SET name = t.name || ' #' || t.id
        FROM (
            SELECT project_id, name FROM api_tokens
            WHERE project_id IS NOT NULL
            GROUP BY project_id, name HAVING COUNT(*) > 1
        ) dup
        WHERE t.project_id = dup.project_id AND t.name = dup.name
          AND t.id NOT IN (
              SELECT MIN(id) FROM api_tokens WHERE project_id = dup.project_id AND name = dup.name
          )
    """)
    op.create_unique_constraint("uq_projects_name", "projects", ["name"])
    op.create_unique_constraint(
        "uq_api_tokens_user_name", "api_tokens", ["user_id", "name"],
    )
    op.create_unique_constraint(
        "uq_api_tokens_project_name", "api_tokens", ["project_id", "name"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_api_tokens_project_name", "api_tokens", type_="unique")
    op.drop_constraint("uq_api_tokens_user_name", "api_tokens", type_="unique")
    op.drop_constraint("uq_projects_name", "projects", type_="unique")
