"""
数据模型定义
使用 SQLAlchemy 2.0 异步 ORM
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    String, Integer, Boolean, DateTime, Text, ForeignKey,
    JSON, Enum, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """基础模型类"""
    pass


class SourceStatus(str, PyEnum):
    """数据源状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class DataSourceType(str, PyEnum):
    """数据源类型"""
    HOTLIST = "hotlist"      # 热榜
    ACCOUNT = "account"      # 社交账号
    VIDEO = "video"          # 短视频
    CUSTOM = "custom"        # 自定义


class CollectorType(str, PyEnum):
    """采集器类型"""
    CONFIGURABLE = "configurable"  # 配置化
    PLUGIN = "plugin"              # 插件化


class CollectStatus(str, PyEnum):
    """采集执行状态"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ChangeType(str, PyEnum):
    """热榜变化类型"""
    NEW = "new"              # 新上榜
    RANK_UP = "rank_up"      # 排名上升
    RANK_DOWN = "rank_down"  # 排名下降
    OFF = "off"              # 下榜


class SourceGroup(Base):
    """数据源分组"""
    __tablename__ = "source_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    collect_interval: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30,
        comment="采集频率（分钟）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=func.now(), onupdate=func.now()
    )

    # 关联关系
    data_sources: Mapped[List["DataSource"]] = relationship(
        "DataSource", back_populates="group"
    )

    def __repr__(self) -> str:
        return f"<SourceGroup(id={self.id}, name={self.name})>"


class DataSource(Base):
    """数据源配置"""
    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_groups.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[DataSourceType] = mapped_column(
        Enum(DataSourceType), nullable=False
    )
    collector_type: Mapped[CollectorType] = mapped_column(
        Enum(CollectorType), nullable=False
    )
    config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="采集配置（URL、解析规则等）"
    )
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5,
        comment="优先级（1-10）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    status: Mapped[SourceStatus] = mapped_column(
        Enum(SourceStatus), nullable=False, default=SourceStatus.ACTIVE
    )
    last_collected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=func.now(), onupdate=func.now()
    )

    # 关联关系
    group: Mapped["SourceGroup"] = relationship(
        "SourceGroup", back_populates="data_sources"
    )
    clues: Mapped[List["Clue"]] = relationship(
        "Clue", back_populates="source"
    )
    collect_logs: Mapped[List["CollectLog"]] = relationship(
        "CollectLog", back_populates="source"
    )

    # 索引
    __table_args__ = (
        Index("ix_data_sources_group_id", "group_id"),
        Index("ix_data_sources_type", "type"),
        Index("ix_data_sources_status", "status"),
        Index("ix_data_sources_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<DataSource(id={self.id}, name={self.name})>"


class Clue(Base):
    """采集线索数据"""
    __tablename__ = "clues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(500), nullable=False,
        comment="标题/内容摘要"
    )
    url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="原始链接"
    )
    cover_image: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="图片/视频封面URL"
    )
    author: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="作者信息"
    )
    rank: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="排名（热榜类）"
    )
    heat_value: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="热度值"
    )
    likes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0
    )
    comments: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0
    )
    shares: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0
    )
    tags: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, default=list,
        comment="话题标签数组"
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    unique_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True,
        comment="去重哈希（标题+作者+来源的MD5）"
    )

    # 关联关系
    source: Mapped["DataSource"] = relationship(
        "DataSource", back_populates="clues"
    )
    hotlist_history: Mapped[List["HotlistHistory"]] = relationship(
        "HotlistHistory", back_populates="clue"
    )

    # 索引
    __table_args__ = (
        Index("ix_clues_source_id", "source_id"),
        Index("ix_clues_collected_at", "collected_at"),
        Index("ix_clues_unique_hash", "unique_hash"),
        Index("ix_clues_source_collected", "source_id", "collected_at"),
    )

    def __repr__(self) -> str:
        return f"<Clue(id={self.id}, title={self.title[:30]}...)>"


class HotlistHistory(Base):
    """热榜变化历史"""
    __tablename__ = "hotlist_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clues.id"), nullable=False
    )
    change_type: Mapped[ChangeType] = mapped_column(
        Enum(ChangeType), nullable=False
    )
    old_rank: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    new_rank: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    # 关联关系
    clue: Mapped["Clue"] = relationship(
        "Clue", back_populates="hotlist_history"
    )

    # 索引
    __table_args__ = (
        Index("ix_hotlist_history_clue_id", "clue_id"),
        Index("ix_hotlist_history_recorded_at", "recorded_at"),
    )

    def __repr__(self) -> str:
        return f"<HotlistHistory(clue_id={self.clue_id}, change={self.change_type})>"


class CollectLog(Base):
    """采集执行日志"""
    __tablename__ = "collect_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False
    )
    status: Mapped[CollectStatus] = mapped_column(
        Enum(CollectStatus), nullable=False
    )
    items_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="采集条数"
    )
    error_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="执行时长（毫秒）"
    )
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, default=dict,
        comment="额外元数据"
    )

    # 关联关系
    source: Mapped["DataSource"] = relationship(
        "DataSource", back_populates="collect_logs"
    )

    # 索引
    __table_args__ = (
        Index("ix_collect_logs_source_id", "source_id"),
        Index("ix_collect_logs_status", "status"),
        Index("ix_collect_logs_started_at", "started_at"),
        Index("ix_collect_logs_source_started", "source_id", "started_at"),
    )

    def __repr__(self) -> str:
        return f"<CollectLog(id={self.id}, status={self.status}, items={self.items_count})>"


class CookieStatus(str, PyEnum):
    """Cookie状态"""
    ACTIVE = "active"      # 可用
    INVALID = "invalid"    # 失效
    EXPIRED = "expired"    # 过期


class CookieEntry(Base):
    """Cookie池条目"""
    __tablename__ = "cookie_pool"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False,
        comment="数据源ID"
    )
    cookies: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="Cookie字典"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Cookie名称/标识"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active",
        comment="状态: active/invalid/expired"
    )
    use_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="使用次数"
    )
    success_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="成功次数"
    )
    fail_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="失败次数"
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="最后使用时间"
    )
    last_success_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="最后成功时间"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="过期时间"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=func.now(), onupdate=func.now()
    )
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="额外数据"
    )

    # 索引
    __table_args__ = (
        Index("ix_cookie_pool_source_id", "source_id"),
        Index("ix_cookie_pool_status", "status"),
        Index("ix_cookie_pool_source_status", "source_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<CookieEntry(id={self.id}, source_id={self.source_id}, status={self.status})>"

    def success_rate(self) -> float:
        """计算成功率"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 1.0
        return self.success_count / total
