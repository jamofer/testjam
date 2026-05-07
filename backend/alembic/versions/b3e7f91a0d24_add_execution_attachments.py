"""add execution_attachments

Revision ID: b3e7f91a0d24
Revises: 537df673456b
Create Date: 2026-05-03 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'b3e7f91a0d24'
down_revision = '537df673456b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'execution_attachments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('execution_id', sa.Integer(), sa.ForeignKey('test_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(128), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(512), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('uploaded_by', sa.String(128), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('execution_attachments')
