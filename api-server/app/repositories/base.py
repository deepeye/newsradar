"""Base repository with generic CRUD"""
from typing import Optional, TypeVar, Type, Sequence
from uuid import UUID

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository:
    """Base repository with common operations"""

    def __init__(self, session: AsyncSession, model_class: Type[ModelType]):
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, item_id: UUID) -> Optional[ModelType]:
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ModelType]:
        result = await self.session.execute(
            select(self.model_class)
            .order_by(self.model_class.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(self.model_class)
        )
        return result.scalar_one()

    async def delete_by_id(self, item_id: UUID) -> bool:
        result = await self.session.execute(
            delete(self.model_class).where(self.model_class.id == item_id)
        )
        return result.rowcount > 0
