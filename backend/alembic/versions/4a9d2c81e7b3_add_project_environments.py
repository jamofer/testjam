"""add project_environments table

Revision ID: 4a9d2c81e7b3
Revises: 9be5727bc584
Create Date: 2026-05-17 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text


revision: str = "4a9d2c81e7b3"
down_revision: Union[str, None] = "9be5727bc584"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_environments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("color", sa.String(length=16), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("project_id", "slug", name="uq_project_environment_slug"),
    )

    op.add_column(
        "app_settings",
        sa.Column(
            "auto_create_environments",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    conn = op.get_bind()
    conn.execute(
        text(
            """
            UPDATE test_executions
            SET environment = LOWER(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(TRIM(environment), '[^A-Za-z0-9_-]+', '-', 'g'),
                    '_', '-', 'g'
                )
            )
            WHERE environment IS NOT NULL AND environment <> ''
            """
        )
    )

    conn.execute(
        text(
            """
            INSERT INTO project_environments
                (project_id, name, slug, "order", is_default, created_at)
            SELECT
                te.project_id,
                te.environment AS name,
                te.environment AS slug,
                ROW_NUMBER() OVER (PARTITION BY te.project_id ORDER BY te.environment) AS "order",
                false,
                NOW()
            FROM (
                SELECT DISTINCT project_id, environment
                FROM test_executions
                WHERE environment IS NOT NULL AND environment <> ''
            ) te
            WHERE NOT EXISTS (
                SELECT 1 FROM project_environments pe
                WHERE pe.project_id = te.project_id AND pe.slug = te.environment
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_column("app_settings", "auto_create_environments")
    op.drop_table("project_environments")
