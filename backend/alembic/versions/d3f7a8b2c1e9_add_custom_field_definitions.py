"""add custom_field_definitions table and custom_fields columns

Revision ID: d3f7a8b2c1e9
Revises: c7d8e9f0a1b2
Create Date: 2026-05-20 02:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d3f7a8b2c1e9"
down_revision: Union[str, None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "custom_field_definitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column(
            "required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("default_value", sa.JSON(), nullable=True),
        sa.Column(
            "position",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "project_id", "entity_type", "key", name="uq_cfd_project_entity_key"
        ),
    )
    op.create_index(
        "ix_custom_field_definitions_project_id",
        "custom_field_definitions",
        ["project_id"],
    )

    op.add_column(
        "bugs",
        sa.Column(
            "custom_fields",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    op.add_column(
        "test_cases",
        sa.Column(
            "custom_fields",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    op.add_column(
        "test_executions",
        sa.Column(
            "custom_fields",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("test_executions", "custom_fields")
    op.drop_column("test_cases", "custom_fields")
    op.drop_column("bugs", "custom_fields")
    op.drop_index(
        "ix_custom_field_definitions_project_id",
        table_name="custom_field_definitions",
    )
    op.drop_table("custom_field_definitions")
