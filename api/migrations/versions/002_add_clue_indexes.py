"""add indexes on clues table for dashboard queries

Revision ID: 002
Revises: 001
"""
from alembic import op

revision = "002"
down_revision = "001_api"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # These indexes may already exist if collector migrations ran first
    op.execute("CREATE INDEX IF NOT EXISTS ix_clues_source_id ON clues (source_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_clues_source_rank ON clues (source_id, \"rank\")")
    op.execute("CREATE INDEX IF NOT EXISTS ix_clues_source_collected ON clues (source_id, collected_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_clues_collected_at ON clues (collected_at)")


def downgrade() -> None:
    op.drop_index("ix_clues_collected_at", table_name="clues")
    op.drop_index("ix_clues_source_collected", table_name="clues")
    op.drop_index("ix_clues_source_rank", table_name="clues")
    op.drop_index("ix_clues_source_id", table_name="clues")