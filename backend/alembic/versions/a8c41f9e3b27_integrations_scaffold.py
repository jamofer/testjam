"""integrations scaffold

Revision ID: a8c41f9e3b27
Revises: f4d27e8b1a35
Create Date: 2026-05-19 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'a8c41f9e3b27'
down_revision: Union[str, None] = 'f4d27e8b1a35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'project_integrations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column('status_mapping', sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.UniqueConstraint(
            'project_id', 'provider', 'name',
            name='uq_project_integrations_project_provider_name',
        ),
    )
    op.create_index(
        'ix_project_integrations_project_id', 'project_integrations', ['project_id'],
    )

    op.create_table(
        'integration_credentials',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('integration_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('kind', sa.String(length=32), nullable=False, server_default='api_token'),
        sa.Column('secret_encrypted', sa.LargeBinary(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(
            ['integration_id'], ['project_integrations.id'], ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'bug_external_links',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('bug_id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=True),
        sa.Column('provider', sa.String(length=32), nullable=True),
        sa.Column('external_id', sa.String(length=128), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('status_raw', sa.String(length=64), nullable=True),
        sa.Column('status_normalized', sa.String(length=16), nullable=False, server_default='unknown'),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['bug_id'], ['bugs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['integration_id'], ['project_integrations.id'], ondelete='SET NULL',
        ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint(
            'bug_id', 'integration_id', 'external_id',
            name='uq_bug_external_links_bug_integration_external',
        ),
    )
    op.create_index('ix_bug_external_links_bug_id', 'bug_external_links', ['bug_id'])
    op.create_index('ix_bug_external_links_integration_id', 'bug_external_links', ['integration_id'])

    # Backfill: existing free-text external_ticket_url becomes a provider-less link.
    op.execute(
        """
        INSERT INTO bug_external_links
            (bug_id, integration_id, provider, external_id, url, status_raw, status_normalized, last_synced_at, created_by_id, created_at)
        SELECT
            id, NULL, NULL, COALESCE(external_ticket_url, ''),
            external_ticket_url, NULL, 'unknown', NULL, NULL, now()
        FROM bugs
        WHERE external_ticket_url IS NOT NULL AND external_ticket_url != ''
        """
    )


def downgrade() -> None:
    op.drop_index('ix_bug_external_links_integration_id', table_name='bug_external_links')
    op.drop_index('ix_bug_external_links_bug_id', table_name='bug_external_links')
    op.drop_table('bug_external_links')
    op.drop_table('integration_credentials')
    op.drop_index('ix_project_integrations_project_id', table_name='project_integrations')
    op.drop_table('project_integrations')
