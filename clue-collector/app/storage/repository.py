"""
数据访问层 - Repository 模式
提供各模型的 CRUD 操作
"""
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Sequence
from uuid import UUID

from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models import (
    SourceGroup, DataSource, Clue, HotlistHistory, CollectLog,
    DataSourceType, CollectorType, SourceStatus, CollectStatus, ChangeType
)


class BaseRepository:
    """基础仓库类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self) -> None:
        """提交事务"""
        await self.session.commit()


class SourceGroupRepository(BaseRepository):
    """数据源分组仓库"""

    async def get_by_id(self, group_id: UUID) -> Optional[SourceGroup]:
        """根据ID获取分组"""
        result = await self.session.execute(
            select(SourceGroup).where(SourceGroup.id == group_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = False) -> Sequence[SourceGroup]:
        """获取所有分组"""
        query = select(SourceGroup)
        if active_only:
            query = query.where(SourceGroup.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, name: str, collect_interval: int = 30) -> SourceGroup:
        """创建分组"""
        group = SourceGroup(
            name=name,
            collect_interval=collect_interval,
            is_active=True
        )
        self.session.add(group)
        await self.session.flush()
        return group

    async def update(self, group_id: UUID, **kwargs) -> Optional[SourceGroup]:
        """更新分组"""
        await self.session.execute(
            update(SourceGroup)
            .where(SourceGroup.id == group_id)
            .values(updated_at=datetime.now(timezone.utc), **kwargs)
        )
        return await self.get_by_id(group_id)

    async def delete(self, group_id: UUID) -> bool:
        """删除分组"""
        result = await self.session.execute(
            delete(SourceGroup).where(SourceGroup.id == group_id)
        )
        return result.rowcount > 0


class DataSourceRepository(BaseRepository):
    """数据源配置仓库"""

    async def get_by_id(self, source_id: UUID) -> Optional[DataSource]:
        """根据ID获取数据源"""
        result = await self.session.execute(
            select(DataSource).where(DataSource.id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_by_group(
        self, group_id: UUID, active_only: bool = False
    ) -> Sequence[DataSource]:
        """获取分组下的数据源"""
        query = select(DataSource).where(DataSource.group_id == group_id)
        if active_only:
            query = query.where(DataSource.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_all_active(self) -> Sequence[DataSource]:
        """获取所有活跃数据源"""
        result = await self.session.execute(
            select(DataSource)
            .where(DataSource.is_active == True)
            .where(DataSource.status.in_([SourceStatus.ACTIVE, SourceStatus.ERROR]))
            .order_by(DataSource.priority.desc())
        )
        return result.scalars().all()

    async def create(
        self,
        group_id: UUID,
        name: str,
        source_type: DataSourceType,
        collector_type: CollectorType,
        config: dict,
        priority: int = 5
    ) -> DataSource:
        """创建数据源"""
        source = DataSource(
            group_id=group_id,
            name=name,
            type=source_type,
            collector_type=collector_type,
            config=config,
            priority=priority,
            is_active=True,
            status=SourceStatus.ACTIVE
        )
        self.session.add(source)
        await self.session.flush()
        return source

    async def update(self, source_id: UUID, **kwargs) -> Optional[DataSource]:
        """更新数据源"""
        await self.session.execute(
            update(DataSource)
            .where(DataSource.id == source_id)
            .values(updated_at=datetime.now(timezone.utc), **kwargs)
        )
        return await self.get_by_id(source_id)

    async def record_success(self, source_id: UUID) -> None:
        """记录采集成功"""
        await self.session.execute(
            update(DataSource)
            .where(DataSource.id == source_id)
            .values(
                last_collected_at=datetime.now(timezone.utc),
                consecutive_failures=0,
                status=SourceStatus.ACTIVE,
                updated_at=datetime.now(timezone.utc)
            )
        )

    async def record_failure(
        self, source_id: UUID, error_message: str
    ) -> None:
        """记录采集失败"""
        source = await self.get_by_id(source_id)
        if source:
            new_failures = source.consecutive_failures + 1
            status = SourceStatus.ERROR if new_failures >= 5 else source.status

            await self.session.execute(
                update(DataSource)
                .where(DataSource.id == source_id)
                .values(
                    last_error_at=datetime.now(timezone.utc),
                    last_error_message=error_message,
                    consecutive_failures=new_failures,
                    status=status,
                    updated_at=datetime.now(timezone.utc)
                )
            )


class ClueRepository(BaseRepository):
    """线索数据仓库"""

    @staticmethod
    def generate_unique_hash(title: str, author: Optional[str], source_id: UUID) -> str:
        """生成去重哈希"""
        content = f"{title}:{author or ''}:{str(source_id)}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    async def get_by_id(self, clue_id: UUID) -> Optional[Clue]:
        """根据ID获取线索"""
        result = await self.session.execute(
            select(Clue).where(Clue.id == clue_id)
        )
        return result.scalar_one_or_none()

    async def get_by_hash(self, unique_hash: str) -> Optional[Clue]:
        """根据哈希获取线索"""
        result = await self.session.execute(
            select(Clue).where(Clue.unique_hash == unique_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_source(
        self,
        source_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[Clue]:
        """获取数据源的所有线索"""
        result = await self.session.execute(
            select(Clue)
            .where(Clue.source_id == source_id)
            .order_by(Clue.collected_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def create(
        self,
        source_id: UUID,
        title: str,
        original_content: Optional[str] = None,
        translated_content: Optional[str] = None,
        url: Optional[str] = None,
        cover_image: Optional[str] = None,
        author: Optional[str] = None,
        rank: Optional[int] = None,
        heat_value: Optional[str] = None,
        likes: Optional[int] = None,
        comments: Optional[int] = None,
        shares: Optional[int] = None,
        tags: Optional[list] = None
    ) -> Clue:
        """创建线索"""
        unique_hash = self.generate_unique_hash(title, author, source_id)

        clue = Clue(
            source_id=source_id,
            title=title,
            original_content=original_content,
            translated_content=translated_content,
            url=url,
            cover_image=cover_image,
            author=author,
            rank=rank,
            heat_value=heat_value,
            likes=likes or 0,
            comments=comments or 0,
            shares=shares or 0,
            tags=tags or [],
            unique_hash=unique_hash
        )
        self.session.add(clue)
        await self.session.flush()
        return clue

    async def create_or_update(
        self,
        source_id: UUID,
        title: str,
        original_content: Optional[str] = None,
        translated_content: Optional[str] = None,
        url: Optional[str] = None,
        cover_image: Optional[str] = None,
        author: Optional[str] = None,
        rank: Optional[int] = None,
        heat_value: Optional[str] = None,
        likes: Optional[int] = None,
        comments: Optional[int] = None,
        shares: Optional[int] = None,
        tags: Optional[list] = None
    ) -> tuple[Clue, bool]:
        """创建或更新线索，返回(线索, 是否新建)"""
        unique_hash = self.generate_unique_hash(title, author, source_id)
        existing = await self.get_by_hash(unique_hash)

        if existing:
            # 更新现有线索
            await self.session.execute(
                update(Clue)
                .where(Clue.id == existing.id)
                .values(
                    rank=rank,
                    heat_value=heat_value,
                    likes=likes or existing.likes,
                    comments=comments or existing.comments,
                    shares=shares or existing.shares,
                    tags=tags or existing.tags,
                    collected_at=datetime.now(timezone.utc)
                )
            )
            updated = await self.get_by_id(existing.id)
            return updated, False
        else:
            # 创建新线索
            clue = await self.create(
                source_id=source_id,
                title=title,
                original_content=original_content,
                translated_content=translated_content,
                url=url,
                cover_image=cover_image,
                author=author,
                rank=rank,
                heat_value=heat_value,
                likes=likes,
                comments=comments,
                shares=shares,
                tags=tags
            )
            return clue, True

    async def bulk_create(self, clues_data: List[dict]) -> List[Clue]:
        """批量创建线索（自动去重）"""
        created_clues = []

        for data in clues_data:
            source_id = data['source_id']
            title = data['title']
            author = data.get('author')

            unique_hash = self.generate_unique_hash(title, author, source_id)
            existing = await self.get_by_hash(unique_hash)

            if not existing:
                clue = await self.create(**data)
                created_clues.append(clue)

        return created_clues


class HotlistHistoryRepository(BaseRepository):
    """热榜变化历史仓库"""

    async def get_by_clue(
        self, clue_id: UUID, limit: int = 100
    ) -> Sequence[HotlistHistory]:
        """获取线索的变化历史"""
        result = await self.session.execute(
            select(HotlistHistory)
            .where(HotlistHistory.clue_id == clue_id)
            .order_by(HotlistHistory.recorded_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def create(
        self,
        clue_id: UUID,
        change_type: ChangeType,
        old_rank: Optional[int] = None,
        new_rank: Optional[int] = None
    ) -> HotlistHistory:
        """创建历史记录"""
        history = HotlistHistory(
            clue_id=clue_id,
            change_type=change_type,
            old_rank=old_rank,
            new_rank=new_rank
        )
        self.session.add(history)
        await self.session.flush()
        return history

    async def record_rank_change(
        self, clue_id: UUID, old_rank: int, new_rank: int
    ) -> Optional[HotlistHistory]:
        """记录排名变化"""
        if old_rank == new_rank:
            return None

        change_type = ChangeType.RANK_UP if new_rank < old_rank else ChangeType.RANK_DOWN
        return await self.create(clue_id, change_type, old_rank, new_rank)


class CollectLogRepository(BaseRepository):
    """采集日志仓库"""

    async def get_by_id(self, log_id: UUID) -> Optional[CollectLog]:
        """根据ID获取日志"""
        result = await self.session.execute(
            select(CollectLog).where(CollectLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_by_source(
        self,
        source_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> Sequence[CollectLog]:
        """获取数据源的采集日志"""
        result = await self.session.execute(
            select(CollectLog)
            .where(CollectLog.source_id == source_id)
            .order_by(CollectLog.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def create(
        self,
        source_id: UUID,
        status: CollectStatus,
        items_count: int = 0,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0,
        duration_ms: Optional[int] = None,
        extra_data: Optional[dict] = None
    ) -> CollectLog:
        """创建采集日志"""
        log = CollectLog(
            source_id=source_id,
            status=status,
            items_count=items_count,
            error_type=error_type,
            error_message=error_message,
            retry_count=retry_count,
            duration_ms=duration_ms,
            extra_data=extra_data or {}
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def finish(
        self,
        log_id: UUID,
        status: CollectStatus,
        items_count: int = 0,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """完成采集日志"""
        log = await self.get_by_id(log_id)
        if log and log.started_at:
            duration_ms = int(
                (datetime.now(timezone.utc) - log.started_at).total_seconds() * 1000
            )
        else:
            duration_ms = None

        await self.session.execute(
            update(CollectLog)
            .where(CollectLog.id == log_id)
            .values(
                status=status,
                items_count=items_count,
                error_type=error_type,
                error_message=error_message,
                finished_at=datetime.now(timezone.utc),
                duration_ms=duration_ms
            )
        )

    async def get_recent_failures(
        self, source_id: UUID, limit: int = 5
    ) -> Sequence[CollectLog]:
        """获取最近失败的日志"""
        result = await self.session.execute(
            select(CollectLog)
            .where(CollectLog.source_id == source_id)
            .where(CollectLog.status == CollectStatus.FAILED)
            .order_by(CollectLog.started_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
