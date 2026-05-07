"""Init API tables

Revision ID: 001_api
Revises:
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '001_api'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False, server_default=''),
        sa.Column('role', sa.String(20), nullable=False, server_default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )

    op.create_table('org_configs',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('domains', JSONB, nullable=False),
        sa.Column('style', JSONB, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('topic_outlines',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('urgency', sa.String(20), nullable=False, server_default='中'),
        sa.Column('info_density', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('headlines', JSONB, nullable=True),
        sa.Column('lead_paragraph', sa.Text(), nullable=True),
        sa.Column('outline_sections', JSONB, nullable=True),
        sa.Column('interview_directions', JSONB, nullable=True),
        sa.Column('references', JSONB, nullable=True),
        sa.Column('source_clue_ids', JSONB, nullable=True),
        sa.Column('ai_model', sa.String(50), nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('articles',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('outline_id', UUID(as_uuid=True), sa.ForeignKey('topic_outlines.id'), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('author_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('target_word_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('urgent', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('ai_suggestions', JSONB, nullable=True),
        sa.Column('metrics', JSONB, nullable=True),
        sa.Column('references', JSONB, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('last_saved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('articles')
    op.drop_table('topic_outlines')
    op.drop_table('org_configs')
    op.drop_table('users')
