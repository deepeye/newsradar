"""refactor cookie_pool: remove source_id, add platform to data_sources

Revision ID: 007
Revises: 006
"""
from alembic import op
import sqlalchemy as sa


revision = "007_refactor_cookie_platform"
down_revision = "006_add_cookie_platform"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add platform column to data_sources
    op.add_column(
        "data_sources",
        sa.Column("platform", sa.String(20), nullable=True, comment="平台标识"),
    )
    op.execute(
        "UPDATE data_sources SET platform = config->>'platform' "
        "WHERE collector_type = 'kol' AND config ? 'platform'"
    )
    op.create_index("ix_data_sources_platform", "data_sources", ["platform"])

    # 2. Remove source_id from cookie_pool
    op.drop_index("ix_cookie_pool_source_id", table_name="cookie_pool")
    op.drop_index("ix_cookie_pool_source_status", table_name="cookie_pool")
    # Drop FK first, then column
    op.drop_constraint("cookie_pool_source_id_fkey", "cookie_pool", type_="foreignkey")
    op.drop_column("cookie_pool", "source_id")


def downgrade() -> None:
    # Re-add source_id to cookie_pool
    op.add_column(
        "cookie_pool",
        sa.Column("source_id", sa.UUID, sa.ForeignKey("data_sources.id"), nullable=False),
    )
    # Backfill source_id from a matching data_source (use first KOL of same platform)
    op.execute(
        "UPDATE cookie_pool SET source_id = ds.id "
        "FROM data_sources ds "
        "WHERE cookie_pool.platform = ds.config->>'platform' "
        "AND ds.collector_type = 'kol' "
        "AND cookie_pool.source_id IS NULL"
    )
    op.create_index("ix_cookie_pool_source_id", "cookie_pool", ["source_id"])
    op.create_index("ix_cookie_pool_source_status", "cookie_pool", ["source_id", "status"])

    # Remove platform from data_sources
    op.drop_index("ix_data_sources_platform", table_name="data_sources")
    op.drop_column("data_sources", "platform")