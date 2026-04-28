"""Article draft model"""
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ArticleStatus(str, PyEnum):
    DRAFT = "draft"
    REVIEWING = "reviewing"
    PUBLISHED = "published"


class Article(BaseModel):
    __tablename__ = "articles"

    outline_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("topic_outlines.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    urgent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_suggestions: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    references: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    status: Mapped[ArticleStatus] = mapped_column(
        String(20), nullable=False, default=ArticleStatus.DRAFT
    )
    last_saved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
