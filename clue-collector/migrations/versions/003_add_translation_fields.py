"""Add translation fields to clues

Revision ID: 003_add_translation
Revises: 002_add_cookie_pool
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_translation'
down_revision = '002_add_cookie_pool'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add original_content and translated_content fields to clues table
    op.add_column('clues', sa.Column('original_content', sa.Text(), nullable=True, comment='原始内容（非中文原文）'))
    op.add_column('clues', sa.Column('translated_content', sa.Text(), nullable=True, comment='翻译后的中文内容'))


def downgrade() -> None:
    # Remove translation fields from clues table
    op.drop_column('clues', 'translated_content')
    op.drop_column('clues', 'original_content')