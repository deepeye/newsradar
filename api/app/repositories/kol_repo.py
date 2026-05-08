"""KOL repository — CRUD operations"""
from typing import Sequence, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kol import KOLProfile, CookieEntry
from app.repositories.base import BaseRepository


class KOLProfileRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, KOLProfile)

    async def get_by_platform_id(self, platform: str, platform_id: str) -> Optional[KOLProfile]:
        result = await self.session.execute(
            select(KOLProfile).where(
                KOLProfile.platform == platform,
                KOLProfile.platform_id == platform_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_platform(self, platform: str, limit: int = 100, offset: int = 0) -> Sequence[KOLProfile]:
        result = await self.session.execute(
            select(KOLProfile)
            .where(KOLProfile.platform == platform)
            .order_by(KOLProfile.created_at.desc())
            .limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def count_by_platform(self, platform: Optional[str] = None) -> int:
        q = select(func.count()).select_from(KOLProfile)
        if platform:
            q = q.where(KOLProfile.platform == platform)
        result = await self.session.execute(q)
        return result.scalar_one()

    async def create(
        self,
        source_id: UUID,
        platform: str,
        platform_id: str,
        screen_name: str,
        avatar_url: str = None,
        bio: str = None,
    ) -> KOLProfile:
        now = datetime.now(timezone.utc)
        profile = KOLProfile(
            id=uuid4(),
            source_id=source_id,
            platform=platform,
            platform_id=platform_id,
            screen_name=screen_name,
            avatar_url=avatar_url,
            bio=bio,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def update(self, kol_id: UUID, **kwargs) -> Optional[KOLProfile]:
        result = await self.session.execute(
            update(KOLProfile).where(KOLProfile.id == kol_id).values(**kwargs).returning(KOLProfile)
        )
        return result.scalar_one_or_none()


class CookieRepository:
    """Simplified cookie repo for KOL cookie management"""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_cookie(self, source_id: UUID, cookies: dict, name: str = None, platform: str = None) -> CookieEntry:
        now = datetime.now(timezone.utc)
        entry = CookieEntry(
            id=uuid4(),
            source_id=source_id,
            cookies=cookies,
            name=name or "imported",
            platform=platform,
            status="active",
            use_count=0,
            success_count=0,
            fail_count=0,
            created_at=now,
            updated_at=now,
        )
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def get_by_source(self, source_id: UUID) -> Sequence[CookieEntry]:
        result = await self.session.execute(
            select(CookieEntry).where(CookieEntry.source_id == source_id).order_by(CookieEntry.created_at.desc())
        )
        return result.scalars().all()

    async def delete_by_id(self, cookie_id: UUID) -> bool:
        result = await self.session.execute(
            delete(CookieEntry).where(CookieEntry.id == cookie_id)
        )
        return result.rowcount > 0
