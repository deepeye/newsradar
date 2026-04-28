"""AI Discovery service"""
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.org_config_repo import OrgConfigRepository
from app.repositories.clue_repo import ClueRepository
from app.services.ai_service import AIService
from app.utils.cache import cache_manager
import structlog

logger = structlog.get_logger("discovery_service")


class DiscoveryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.org_config_repo = OrgConfigRepository(db)
        self.clue_repo = ClueRepository(db)
        self.ai_service = AIService()

    async def get_config(self) -> Optional[dict]:
        config = await self.org_config_repo.get_active()
        if not config:
            return None
        return {
            "id": str(config.id),
            "name": config.name,
            "domains": config.domains,
            "style": config.style,
        }

    async def update_config(self, name: Optional[str], domains: Optional[list], style: Optional[list]) -> dict:
        active = await self.org_config_repo.get_active()
        config_name = name or (active.name if active else "Default")
        config_domains = domains or (active.domains if active else [])
        config_style = style or (active.style if active else [])

        config = await self.org_config_repo.create_or_update(
            name=config_name,
            domains=config_domains,
            style=config_style,
        )
        # Invalidate cached recommendations
        await cache_manager.delete("discovery:recommendations")
        return {
            "id": str(config.id),
            "name": config.name,
            "domains": config.domains,
            "style": config.style,
        }

    async def get_recommendations(self, force_refresh: bool = False) -> dict:
        cache_key = "discovery:recommendations"

        if not force_refresh:
            cached = await cache_manager.get(cache_key)
            if cached:
                return cached

        org_config = await self.org_config_repo.get_active()
        if not org_config:
            return {
                "org_config": {"id": "", "name": "", "domains": [], "style": []},
                "total_clues": 0,
                "last_updated": "",
                "recommendations": [],
                "total_recommendations": 0,
            }

        total_clues = await self.clue_repo.count_total()
        clues = await self.clue_repo.get_all(limit=50)

        clues_text = "\n".join(
            f"{i+1}. [{c.author or '未知'}] {c.title} (热度: {c.heat_value or 'N/A'})"
            for i, c in enumerate(clues[:30])
        )

        try:
            raw_recommendations = await self.ai_service.generate_topic_recommendations(
                domains=org_config.domains,
                style=org_config.style,
                clues_text=clues_text,
                limit=10,
            )
        except Exception as e:
            logger.error("discovery_ai_failed", error=str(e))
            raw_recommendations = []

        recommendations = []
        for i, r in enumerate(raw_recommendations):
            recommendations.append({
                "id": f"rec{i+1}",
                "source": r.get("source", ""),
                "source_icon": r.get("source_icon", "newspaper"),
                "tag": r.get("tag", ""),
                "title": r.get("title", ""),
                "reason": r.get("reason", ""),
                "angles": r.get("angles", []),
            })

        result = {
            "org_config": {
                "id": str(org_config.id),
                "name": org_config.name,
                "domains": org_config.domains,
                "style": org_config.style,
            },
            "total_clues": total_clues,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
        }

        await cache_manager.set(cache_key, result, ttl=300)
        return result