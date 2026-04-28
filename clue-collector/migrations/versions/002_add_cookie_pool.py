"""add cookie_pool table

Revision ID: 002
Revises: 001_init_db
Create Date: 2026-04-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建Cookie池表
    op.create_table(
        'cookie_pool',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', UUID(as_uuid=True), sa.ForeignKey('data_sources.id'), nullable=False),
        sa.Column('cookies', JSONB, nullable=False, comment='Cookie字典'),
        sa.Column('name', sa.String(100), nullable=True, comment='Cookie名称/标识'),
        sa.Column('status', sa.String(20), nullable=False, default='active', comment='状态: active/invalid/expired'),
        sa.Column('use_count', sa.Integer, nullable=False, default=0, comment='使用次数'),
        sa.Column('success_count', sa.Integer, nullable=False, default=0, comment='成功次数'),
        sa.Column('fail_count', sa.Integer, nullable=False, default=0, comment='失败次数'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True, comment='最后使用时间'),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True, comment='最后成功时间'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='过期时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('extra_data', JSONB, nullable=True, comment='额外数据'),
    )

    # 创建索引
    op.create_index('ix_cookie_pool_source_id', 'cookie_pool', ['source_id'])
    op.create_index('ix_cookie_pool_status', 'cookie_pool', ['status'])
    op.create_index('ix_cookie_pool_source_status', 'cookie_pool', ['source_id', 'status'])


def downgrade() -> None:
    op.drop_index('ix_cookie_pool_source_status', 'cookie_pool')
    op.drop_index('ix_cookie_pool_status', 'cookie_pool')
    op.drop_index('ix_cookie_pool_source_id', 'cookie_pool')
    op.drop_table('cookie_pool')