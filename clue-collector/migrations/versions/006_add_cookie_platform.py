"""add platform column to cookie_pool for shared cookies

Revision ID: 006
Revises: 005
"""
from alembic import op
import sqlalchemy as sa

revision = "006_add_cookie_platform"
down_revision = "005_add_schedule_time"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cookie_pool",
        sa.Column("platform", sa.String(20), nullable=True, comment="平台标识，用于跨数据源共享Cookie"),
    )

    # Backfill platform from data_sources.config
    op.execute(
        "UPDATE cookie_pool SET platform = ds.config->>'platform' "
        "FROM data_sources ds WHERE cookie_pool.source_id = ds.id"
    )

    op.create_index(
        "ix_cookie_pool_platform_status",
        "cookie_pool",
        ["platform", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_cookie_pool_platform_status", table_name="cookie_pool")
    op.drop_column("cookie_pool", "platform")