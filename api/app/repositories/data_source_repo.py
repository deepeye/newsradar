"""Data source repository — CRUD operations"""
from typing import Sequence, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clue import DataSource, SourceGroup
from app.repositories.base import BaseRepository


class SourceGroupRepository(BaseRepository):
    """Source group repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SourceGroup)

    async def get_all_active(self) -> Sequence[SourceGroup]:
        result = await self.session.execute(
            select(SourceGroup)
            .where(SourceGroup.is_active == True)
            .order_by(SourceGroup.created_at.desc())
        )
        return result.scalars().all()

    async def create(
        self,
        name: str,
        collect_interval: int,
        is_active: bool = True,
    ) -> SourceGroup:
        group = SourceGroup(
            name=name,
            collect_interval=collect_interval,
            is_active=is_active,
        )
        self.session.add(group)
        await self.session.flush()
        await self.session.refresh(group)
        return group

    async def update(
        self,
        group_id: UUID,
        **kwargs,
    ) -> Optional[SourceGroup]:
        result = await self.session.execute(
            update(SourceGroup)
            .where(SourceGroup.id == group_id)
            .values(**kwargs)
            .returning(SourceGroup)
        )
        return result.scalar_one_or_none()


class DataSourceRepository(BaseRepository):
    """Data source repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, DataSource)

    async def get_all_active(self) -> Sequence[DataSource]:
        result = await self.session.execute(
            select(DataSource)
            .where(DataSource.is_active == True)
            .where(DataSource.status == "active")
            .order_by(DataSource.priority.desc())
        )
        return result.scalars().all()

    async def get_by_group(self, group_id: UUID) -> Sequence[DataSource]:
        result = await self.session.execute(
            select(DataSource)
            .where(DataSource.group_id == group_id)
            .order_by(DataSource.priority.desc())
        )
        return result.scalars().all()

    async def create(
        self,
        group_id: UUID,
        name: str,
        type: str,
        collector_type: str,
        config: dict,
        priority: int = 5,
        is_active: bool = True,
    ) -> DataSource:
        source = DataSource(
            group_id=group_id,
            name=name,
            type=type,
            collector_type=collector_type,
            config=config,
            priority=priority,
            is_active=is_active,
            status="active",
        )
        self.session.add(source)
        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def update(
        self,
        source_id: UUID,
        **kwargs,
    ) -> Optional[DataSource]:
        result = await self.session.execute(
            update(DataSource)
            .where(DataSource.id == source_id)
            .values(**kwargs)
            .returning(DataSource)
        )
        return result.scalar_one_or_none()

    async def count_by_group(self, group_id: UUID) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).select_from(DataSource)
            .where(DataSource.group_id == group_id)
        )
        return result.scalar_one()