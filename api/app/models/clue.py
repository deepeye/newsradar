"""Clue model — mapping to clue-collector tables"""
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SourceStatus(str, PyEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class DataSourceType(str, PyEnum):
    HOTLIST = "hotlist"
    ACCOUNT = "account"
    VIDEO = "video"
    CUSTOM = "custom"


class CollectorType(str, PyEnum):
    CONFIGURABLE = "configurable"
    PLUGIN = "plugin"
    KOL = "kol"


class Clue(Base):
    """Read-only mapping — do NOT create migrations for this table"""
    __tablename__ = "clues"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    original_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    translated_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    heat_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    likes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    shares: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    unique_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class SourceGroup(Base):
    """Source group model"""
    __tablename__ = "source_groups"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    collect_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )

    # Relationships
    data_sources: Mapped[list["DataSource"]] = relationship(
        "DataSource", back_populates="group"
    )


class DataSource(Base):
    """Data source model"""
    __tablename__ = "data_sources"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    group_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("source_groups.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[DataSourceType] = mapped_column(Enum(DataSourceType), nullable=False)
    collector_type: Mapped[str] = mapped_column(String(20), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[SourceStatus] = mapped_column(Enum(SourceStatus), nullable=False, default=SourceStatus.ACTIVE)
    last_collected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )

    # Relationships
    group: Mapped["SourceGroup"] = relationship(
        "SourceGroup", back_populates="data_sources"
    )