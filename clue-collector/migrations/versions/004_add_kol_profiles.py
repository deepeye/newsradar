"""add kol_profiles table

Revision ID: 004
Revises: 003
Create Date: 2026-04-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '004_add_kol_profiles'
down_revision = '003_add_translation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 kol 值到 collectortype 枚举
    op.execute("ALTER TABLE data_sources ALTER COLUMN collector_type TYPE VARCHAR(20)")
    op.execute("ALTER TABLE data_sources ALTER COLUMN collector_type DROP DEFAULT")

    # 创建 kol_profiles 表
    op.create_table(
        'kol_profiles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', UUID(as_uuid=True), sa.ForeignKey('data_sources.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('platform', sa.String(20), nullable=False, comment='平台: weibo/x'),
        sa.Column('platform_id', sa.String(100), nullable=False, comment='平台用户ID'),
        sa.Column('screen_name', sa.String(100), nullable=False),
        sa.Column('avatar_url', sa.Text, nullable=True),
        sa.Column('bio', sa.Text, nullable=True),
        sa.Column('follower_count', sa.Integer, nullable=True),
        sa.Column('following_count', sa.Integer, nullable=True),
        sa.Column('post_count', sa.Integer, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 创建索引
    op.create_index('ix_kol_profiles_source_id', 'kol_profiles', ['source_id'], unique=True)
    op.create_index('ix_kol_profiles_platform', 'kol_profiles', ['platform'])
    op.create_index('uq_kol_profiles_platform_id', 'kol_profiles', ['platform', 'platform_id'], unique=True)


def downgrade() -> None:
    op.drop_index('uq_kol_profiles_platform_id', 'kol_profiles')
    op.drop_index('ix_kol_profiles_platform', 'kol_profiles')
    op.drop_index('ix_kol_profiles_source_id', 'kol_profiles')
    op.drop_table('kol_profiles')
