"""Dashboard data aggregation service"""
import asyncio
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db_manager
from app.repositories.clue_repo import ClueRepository, DataSourceRepository, SourceGroupRepository
from app.services.ai_service import AIService
from app.utils.cache import cache_manager
from app.core.config import settings
import structlog

logger = structlog.get_logger("dashboard_service")

PLATFORM_LABELS = {
    "weibo": "微博热搜",
    "douyin": "抖音热榜",
    "zhihu": "知乎热榜",
    "baidu": "百度热搜",
    "bilibili": "B站热门",
    "toutiao": "今日头条",
}


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.clue_repo = ClueRepository(db)
        self.source_repo = DataSourceRepository(db)
        self.group_repo = SourceGroupRepository(db)

    async def get_dashboard_data(self, org_config: Optional[dict] = None) -> dict:
        cache_key = "dashboard:data"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        # Fetch sources once, shared by trending + KOL (eliminates duplicate query)
        sources = await self.source_repo.get_all_active()

        # DB tasks are sequential (same session), but batch queries eliminated N+1
        trending_cards = await self._build_trending_cards(sources)
        kol_columns = await self._build_kol_columns(sources)
        stats = await self._build_stats()

        # AI suggestions: non-blocking — return cache or empty, refresh in background
        ai_suggestions = await self._get_ai_suggestions_nonblocking(org_config)

        result = {
            "trending_cards": trending_cards,
            "kol_columns": kol_columns,
            "ai_suggestions": ai_suggestions,
            "active_threads": stats["active_threads"],
            "topic_alerts": stats["topic_alerts"],
            "quote": stats["quote"],
        }

        await cache_manager.set(cache_key, result, ttl=120)
        return result

    async def _build_trending_cards(self, sources) -> list[dict]:
        # Batch-fetch all hot clues at once instead of N+1
        source_ids = [s.id for s in sources]
        all_hot_clues = await self.clue_repo.get_hot_by_sources(source_ids, limit=10)

        cards = []
        for source in sources:
            platform = source.config.get("platform", source.name.lower()) if isinstance(source.config, dict) else source.name.lower()
            clues = all_hot_clues.get(str(source.id), [])

            items = []
            for clue in clues:
                status = "stable"
                if clue.rank and clue.rank <= 3:
                    status = "explosive"
                items.append({
                    "id": str(clue.id),
                    "rank": clue.rank or 0,
                    "title": clue.title,
                    "heat_value": clue.heat_value or "",
                    "status": status,
                    "url": clue.url,
                })

            if items:
                cards.append({
                    "platform": platform,
                    "platform_label": PLATFORM_LABELS.get(platform, source.name),
                    "items": items,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                })

        return cards

    async def _build_kol_columns(self, sources) -> list[dict]:
        kol_sources = [s for s in sources if s.type == "account"]
        if not kol_sources:
            return []

        # Batch-fetch all KOL clues at once
        kol_source_ids = [s.id for s in kol_sources]
        all_kol_clues = await self.clue_repo.get_latest_by_sources(kol_source_ids, limit=5)

        columns = []
        for source in kol_sources:
            clues = all_kol_clues.get(str(source.id), [])
            posts = []
            for clue in clues:
                posts.append({
                    "id": str(clue.id),
                    "author": clue.author or source.name,
                    "verified": True,
                    "content": clue.title,
                    "likes": clue.likes or 0,
                    "shares": clue.shares or 0,
                    "comments": clue.comments or 0,
                    "time_ago": "",
                })
            if posts:
                columns.append({
                    "platform": source.config.get("platform", "weibo") if isinstance(source.config, dict) else "weibo",
                    "platform_label": f"{source.name} KOL",
                    "posts": posts,
                })
        return columns

    async def _get_ai_suggestions_nonblocking(self, org_config: Optional[dict]) -> list[dict]:
        """Return cached AI suggestions immediately; refresh in background if stale."""
        ai_cache_key = "dashboard:ai_suggestions"
        cached = await cache_manager.get(ai_cache_key)
        if cached is not None:
            return cached

        if not org_config:
            return []

        # No cache — trigger background refresh, return empty for now
        asyncio.create_task(self._refresh_ai_suggestions(org_config, ai_cache_key))
        logger.info("dashboard_ai_suggestions_refreshing_background")
        return []

    async def _refresh_ai_suggestions(self, org_config: dict, cache_key: str) -> None:
        """Background task to fetch AI suggestions and update cache."""
        try:
            async with db_manager.session() as session:
                clue_repo = ClueRepository(session)
                ai_service = AIService()
                clues = await clue_repo.get_all(limit=50)
                clues_text = "\n".join(
                    f"{i+1}. {c.title} (热度: {c.heat_value or 'N/A'})"
                    for i, c in enumerate(clues[:20])
                )
                recommendations = await ai_service.generate_topic_recommendations(
                    domains=org_config.get("domains", []),
                    style=org_config.get("style", []),
                    clues_text=clues_text,
                    limit=2,
                )
                suggestions = [
                    {
                        "id": f"ai{i+1}",
                        "title": r.get("title", ""),
                        "description": r.get("reason", ""),
                    }
                    for i, r in enumerate(recommendations)
                ]
                await cache_manager.set(cache_key, suggestions, ttl=300)
                # Invalidate dashboard cache so next request picks up fresh AI suggestions
                await cache_manager.delete("dashboard:data")
                logger.info("dashboard_ai_suggestions_refreshed")
        except Exception as e:
            logger.error("dashboard_ai_suggestions_refresh_failed", error=str(e))

    async def _build_stats(self) -> dict:
        total_clues = await self.clue_repo.count_total()
        return {
            "active_threads": total_clues,
            "topic_alerts": min(total_clues // 1000, 50),
            "quote": {
                "text": "权威性来源于数据的密度与筛选的精准度。",
                "source": "AI 洞察",
            },
        }