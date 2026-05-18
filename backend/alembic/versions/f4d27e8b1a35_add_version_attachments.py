"""add version attachments

Revision ID: f4d27e8b1a35
Revises: e6a3c19f4d72
Create Date: 2026-05-18 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'f4d27e8b1a35'
down_revision: Union[str, None] = 'e6a3c19f4d72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'version_attachments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=128), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['version_id'], ['project_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index(
        'ix_version_attachments_version_id',
        'version_attachments',
        ['version_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_version_attachments_version_id', table_name='version_attachments')
    op.drop_table('version_attachments')
