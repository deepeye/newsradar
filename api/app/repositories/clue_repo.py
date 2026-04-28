"""Clue repository — read-only access to clue-collector tables"""
from typing import Sequence, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clue import Clue, DataSource, SourceGroup
from app.repositories.base import BaseRepository


class ClueRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Clue)

    async def get_latest_by_source(
        self,
        source_id: UUID,
        limit: int = 20,
    ) -> Sequence[Clue]:
        result = await self.session.execute(
            select(Clue)
            .where(Clue.source_id == source_id)
            .order_by(Clue.collected_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_hot_by_source(
        self,
        source_id: UUID,
        limit: int = 10,
    ) -> Sequence[Clue]:
        result = await self.session.execute(
            select(Clue)
            .where(Clue.source_id == source_id)
            .order_by(Clue.rank.asc().nulls_last())
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_source(self, source_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Clue)
            .where(Clue.source_id == source_id)
        )
        return result.scalar_one()

    async def count_total(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Clue)
        )
        return result.scalar_one()

    async def get_by_ids(self, clue_ids: list[UUID]) -> Sequence[Clue]:
        result = await self.session.execute(
            select(Clue).where(Clue.id.in_(clue_ids))
        )
        return result.scalars().all()


class DataSourceRepository(BaseRepository):
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
            .where(DataSource.is_active == True)
        )
        return result.scalars().all()


class SourceGroupRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SourceGroup)

    async def get_all_active(self) -> Sequence[SourceGroup]:
        result = await self.session.execute(
            select(SourceGroup).where(SourceGroup.is_active == True)
        )
        return result.scalars().all()
