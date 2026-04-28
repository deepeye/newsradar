"""Organization configuration repository"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org_config import OrgConfig
from app.repositories.base import BaseRepository


class OrgConfigRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, OrgConfig)

    async def get_active(self) -> Optional[OrgConfig]:
        result = await self.session.execute(
            select(OrgConfig).where(OrgConfig.is_active == True).limit(1)
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        name: str,
        domains: list,
        style: list,
    ) -> OrgConfig:
        existing = await self.get_active()
        if existing:
            existing.name = name
            existing.domains = domains
            existing.style = style
            await self.session.flush()
            return existing
        config = OrgConfig(
            name=name,
            domains=domains,
            style=style,
            is_active=True,
        )
        self.session.add(config)
        await self.session.flush()
        return config
