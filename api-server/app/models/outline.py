"""Topic outline model"""
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class OutlineStatus(str, PyEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    ARCHIVED = "archived"


class TopicOutline(BaseModel):
    __tablename__ = "topic_outlines"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    urgency: Mapped[str] = mapped_column(String(20), nullable=False, default="中")
    info_density: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    headlines: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    lead_paragraph: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outline_sections: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    interview_directions: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    references: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    source_clue_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[OutlineStatus] = mapped_column(
        String(20), nullable=False, default=OutlineStatus.DRAFT
    )
