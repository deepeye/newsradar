"""User repository"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        username: str,
        password_hash: str,
        display_name: str = "",
        role: UserRole = UserRole.VIEWER,
    ) -> User:
        user = User(
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()
        return user
