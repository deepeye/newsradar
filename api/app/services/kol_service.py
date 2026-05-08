"""KOL management service"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.kol_repo import KOLProfileRepository, CookieRepository
from app.repositories.data_source_repo import SourceGroupRepository, DataSourceRepository
from app.models.clue import DataSourceType, CollectorType, Clue, SourceStatus
from app.models.kol import KOLProfile, CookieEntry
from app.schemas.kol import (
    KOLResponse, KOLCreate, KOLUpdate,
    KOLListResponse, KOLPostResponse, KOLPostListResponse,
)
from app.core.exceptions import NotFoundException


KOL_GROUP_NAME = "KOL监控"


class KOLService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.kol_repo = KOLProfileRepository(session)
        self.cookie_repo = CookieRepository(session)
        self.group_repo = SourceGroupRepository(session)
        self.source_repo = DataSourceRepository(session)

    async def _get_or_create_kol_group(self) -> UUID:
        """Get or create the KOL source group"""
        groups = await self.group_repo.get_all_active()
        for g in groups:
            if g.name == KOL_GROUP_NAME:
                return g.id
        group = await self.group_repo.create(name=KOL_GROUP_NAME, collect_interval=30)
        return group.id

    async def list_kols(
        self, platform: Optional[str] = None, page: int = 1, page_size: int = 20,
    ) -> KOLListResponse:
        offset = (page - 1) * page_size
        if platform:
            profiles = await self.kol_repo.get_by_platform(platform, limit=page_size, offset=offset)
            total = await self.kol_repo.count_by_platform(platform)
        else:
            profiles = await self.kol_repo.get_all(limit=page_size, offset=offset)
            total = await self.kol_repo.count_by_platform()

        items = []
        for p in profiles:
            cookie_status = await self._get_cookie_status(p.source_id)
            items.append(self._to_response(p, cookie_status))

        return KOLListResponse(total=total, items=items)

    async def get_kol(self, kol_id: UUID) -> KOLResponse:
        profile = await self.kol_repo.get_by_id(kol_id)
        if not profile:
            raise NotFoundException("KOL profile not found")
        cookie_status = await self._get_cookie_status(profile.source_id)
        return self._to_response(profile, cookie_status)

    async def create_kol(self, request: KOLCreate) -> KOLResponse:
        # Check duplicate
        existing = await self.kol_repo.get_by_platform_id(request.platform, request.platform_id)
        if existing:
            raise NotFoundException(f"KOL {request.platform}/{request.platform_id} already exists")

        # Get or create KOL group
        group_id = await self._get_or_create_kol_group()

        # Create DataSource
        source = await self.source_repo.create(
            group_id=group_id,
            name=f"{request.platform}:{request.screen_name}",
            type=DataSourceType.ACCOUNT,
            collector_type=CollectorType.KOL,
            config={
                "platform": request.platform,
                "platform_id": request.platform_id,
                "screen_name": request.screen_name,
            },
        )

        # Create KOLProfile
        profile = await self.kol_repo.create(
            source_id=source.id,
            platform=request.platform,
            platform_id=request.platform_id,
            screen_name=request.screen_name,
            avatar_url=request.avatar_url,
            bio=request.bio,
        )

        # Import cookies if provided
        if request.cookies:
            await self.cookie_repo.add_cookie(source.id, request.cookies, platform=request.platform)

        await self.session.commit()

        cookie_status = await self._get_cookie_status(source.id)
        return self._to_response(profile, cookie_status)

    async def update_kol(self, kol_id: UUID, request: KOLUpdate) -> KOLResponse:
        update_data = request.model_dump(exclude_none=True)
        if not update_data:
            raise NotFoundException("No update data provided")

        profile = await self.kol_repo.update(kol_id, **update_data)
        if not profile:
            raise NotFoundException("KOL profile not found")

        # Also update DataSource name if screen_name changed
        if request.screen_name:
            platform = profile.platform
            await self.source_repo.update(
                profile.source_id, name=f"{platform}:{request.screen_name}"
            )
            # Update config screen_name too
            source = await self.source_repo.get_by_id(profile.source_id)
            if source:
                config = dict(source.config)
                config["screen_name"] = request.screen_name
                await self.source_repo.update(profile.source_id, config=config)

        # Toggle is_active on DataSource too
        if request.is_active is not None:
            await self.source_repo.update(profile.source_id, is_active=request.is_active)

        await self.session.commit()

        cookie_status = await self._get_cookie_status(profile.source_id)
        return self._to_response(profile, cookie_status)

    async def delete_kol(self, kol_id: UUID) -> bool:
        profile = await self.kol_repo.get_by_id(kol_id)
        if not profile:
            raise NotFoundException("KOL profile not found")

        source_id = profile.source_id
        # Delete KOLProfile (cascades to DataSource via FK)
        deleted = await self.kol_repo.delete_by_id(kol_id)
        if deleted:
            # DataSource is deleted by CASCADE; cookies too
            await self.session.commit()
        return deleted

    async def import_cookies(self, kol_id: UUID, cookies: dict) -> dict:
        profile = await self.kol_repo.get_by_id(kol_id)
        if not profile:
            raise NotFoundException("KOL profile not found")

        entry = await self.cookie_repo.add_cookie(profile.source_id, cookies, platform=profile.platform)
        await self.session.commit()
        return {"id": str(entry.id), "status": entry.status}

    async def import_platform_cookies(self, platform: str, cookies: dict) -> dict:
        """Import cookies for a platform (shared across all KOLs of that platform)"""
        # Find any KOL of this platform to use its source_id
        profiles = await self.kol_repo.get_by_platform(platform, limit=1)
        if not profiles:
            raise NotFoundException(f"No KOL found for platform {platform}")
        source_id = profiles[0].source_id
        entry = await self.cookie_repo.add_cookie(source_id, cookies, platform=platform)
        await self.session.commit()
        return {"id": str(entry.id), "status": entry.status}

    async def delete_cookie(self, kol_id: UUID, cookie_id: UUID) -> bool:
        profile = await self.kol_repo.get_by_id(kol_id)
        if not profile:
            raise NotFoundException("KOL profile not found")

        deleted = await self.cookie_repo.delete_by_id(cookie_id)
        if deleted:
            await self.session.commit()
        return deleted

    async def delete_cookie_by_id(self, cookie_id: UUID) -> bool:
        """Delete a cookie by its ID without requiring a KOL ID"""
        deleted = await self.cookie_repo.delete_by_id(cookie_id)
        if deleted:
            await self.session.commit()
        return deleted

    async def list_posts(
        self, kol_id: UUID, page: int = 1, page_size: int = 20,
    ) -> KOLPostListResponse:
        profile = await self.kol_repo.get_by_id(kol_id)
        if not profile:
            raise NotFoundException("KOL profile not found")

        offset = (page - 1) * page_size
        # Query clues for this KOL's source
        count_result = await self.session.execute(
            select(func.count()).select_from(Clue).where(Clue.source_id == profile.source_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Clue)
            .where(Clue.source_id == profile.source_id)
            .order_by(Clue.collected_at.desc())
            .limit(page_size).offset(offset)
        )
        clues = result.scalars().all()

        items = [
            KOLPostResponse(
                id=str(c.id),
                content=c.title,
                url=c.url,
                author=c.author,
                likes=c.likes or 0,
                comments=c.comments or 0,
                shares=c.shares or 0,
                cover_image=c.cover_image,
                collected_at=c.collected_at,
            )
            for c in clues
        ]
        return KOLPostListResponse(total=total, items=items)

    async def list_all_cookies(self) -> list:
        """List all cookies grouped by platform"""
        platforms = ["x", "weibo"]
        result = []
        for platform in platforms:
            cookies = await self.cookie_repo.get_by_platform(platform)
            result.append({
                "platform": platform,
                "cookies": [
                    {
                        "id": str(c.id),
                        "name": c.name,
                        "status": c.status,
                        "created_at": c.created_at.isoformat() if c.created_at else None,
                        "last_used_at": c.last_used_at.isoformat() if c.last_used_at else None,
                    }
                    for c in cookies
                ]
            })
        return result

    async def _get_cookie_status(self, source_id) -> dict:
        """Count cookies by status for a source"""
        entries = await self.cookie_repo.get_by_source(source_id)
        active = sum(1 for e in entries if e.status == "active")
        invalid = sum(1 for e in entries if e.status == "invalid")
        expired = sum(1 for e in entries if e.status == "expired")
        return {"active": active, "invalid": invalid, "expired": expired}

    def _to_response(self, profile: KOLProfile, cookie_status: dict = None) -> KOLResponse:
        return KOLResponse(
            id=str(profile.id),
            source_id=str(profile.source_id),
            platform=profile.platform,
            platform_id=profile.platform_id,
            screen_name=profile.screen_name,
            avatar_url=profile.avatar_url,
            bio=profile.bio,
            follower_count=profile.follower_count,
            following_count=profile.following_count,
            post_count=profile.post_count,
            is_active=profile.is_active,
            last_synced_at=profile.last_synced_at,
            cookie_status=cookie_status,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
