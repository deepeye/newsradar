"""Outline repository"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outline import TopicOutline, OutlineStatus
from app.repositories.base import BaseRepository


class OutlineRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TopicOutline)

    async def create(
        self,
        title: str,
        summary: Optional[str] = None,
        urgency: str = "中",
        created_by: Optional[UUID] = None,
        **kwargs,
    ) -> TopicOutline:
        outline = TopicOutline(
            title=title,
            summary=summary,
            urgency=urgency,
            created_by=created_by,
            status=OutlineStatus.DRAFT,
            **kwargs,
        )
        self.session.add(outline)
        await self.session.flush()
        return outline

    async def update(self, outline_id: UUID, **kwargs) -> Optional[TopicOutline]:
        outline = await self.get_by_id(outline_id)
        if outline:
            for key, value in kwargs.items():
                if hasattr(outline, key) and value is not None:
                    setattr(outline, key, value)
            await self.session.flush()
        return outline
