"""add schedule_time to source_groups

Revision ID: 005
Revises: 004
"""
from alembic import op
import sqlalchemy as sa

revision = "005_add_schedule_time"
down_revision = "004_add_kol_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "source_groups",
        sa.Column("schedule_time", sa.String(5), nullable=True, comment="定时采集时间 HH:MM（北京时间）"),
    )


def downgrade() -> None:
    op.drop_column("source_groups", "schedule_time")
