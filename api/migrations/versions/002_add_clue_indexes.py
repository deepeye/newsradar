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
    op.create_index("ix_clues_source_id", "clues", ["source_id"])
    op.create_index("ix_clues_source_rank", "clues", ["source_id", op.text('"rank"')])
    op.create_index("ix_clues_source_collected", "clues", ["source_id", "collected_at"])
    op.create_index("ix_clues_collected_at", "clues", ["collected_at"])


def downgrade() -> None:
    op.drop_index("ix_clues_collected_at", table_name="clues")
    op.drop_index("ix_clues_source_collected", table_name="clues")
    op.drop_index("ix_clues_source_rank", table_name="clues")
    op.drop_index("ix_clues_source_id", table_name="clues")
