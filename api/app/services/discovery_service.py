"""AI Discovery service"""
import asyncio
import math
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.org_config_repo import OrgConfigRepository
from app.repositories.clue_repo import ClueRepository, DataSourceRepository
from app.services.ai_service import AIService
from app.utils.cache import cache_manager
from app.utils.heat_value import parse_heat_value
from app.utils.domain_taxonomy import classify_domains, resolve_domain
from app.core.database import db_manager
from app.models.clue import DataSourceType
import structlog

logger = structlog.get_logger("discovery_service")

# Stale-while-revalidate: return cached data up to this age without revalidating
FRESH_TTL = 300  # 5 min — data is considered fresh
STALE_TTL = 600  # 10 min — serve stale data while refreshing in background

# Stratified sampling quotas
HOTLIST_QUOTA = 18  # 60% — trending sources
ACCOUNT_QUOTA = 12  # 40% — KOL/authoritative sources

# Per-source fetch limits (pool ~50 before scoring)
HOTLIST_PER_SOURCE = 8
ACCOUNT_PER_SOURCE = 5

# Minimum pool after domain filter — fall back to unfiltered if too few
MIN_FILTERED_POOL = 10

# Topic merge: minimum common substring length to consider two titles "same topic"
SIMILAR_TITLE_MIN_LEN = 4

# Per-clue AI generation: max concurrent Qwen calls
MAX_CONCURRENT_AI_CALLS = 5

# Final recommendation limit
MAX_RECOMMENDATIONS = 10

# Scoring weights
W_FRESHNESS = 0.3
W_SPREAD = 0.3
W_AUTHORITY = 0.2
W_DOMAIN_RELEVANCE = 0.2

# Platform labels for prompt enrichment
PLATFORM_LABELS = {
    "weibo": "微博",
    "zhihu": "知乎",
    "douyin": "抖音",
    "xiaohongshu": "小红书",
    "bilibili": "B站",
    "toutiao": "今日头条",
    "twitter": "X/Twitter",
    "baidu": "百度",
    "toutiao_hot": "今日头条",
}


class DiscoveryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.org_config_repo = OrgConfigRepository(db)
        self.clue_repo = ClueRepository(db)
        self.ds_repo = DataSourceRepository(db)
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
        await cache_manager.delete("discovery:recommendations")
        return {
            "id": str(config.id),
            "name": config.name,
            "domains": config.domains,
            "style": config.style,
        }

    async def get_recommendations(self, force_refresh: bool = False) -> dict:
        cache_key = "discovery:recommendations"

        if force_refresh:
            return await self._generate_and_cache()

        cached, ttl = await cache_manager.get_with_ttl(cache_key)

        if cached is not None:
            if ttl is not None and ttl > 0 and ttl > (STALE_TTL - FRESH_TTL):
                # Fresh enough — return immediately
                return cached
            # Stale but available — return now, refresh background
            self._schedule_refresh()
            return cached

        # No cache at all — must generate (first-time load)
        return await self._generate_and_cache()

    async def _generate_and_cache(self) -> dict:
        cache_key = "discovery:recommendations"
        org_config = await self.org_config_repo.get_active()
        if not org_config:
            return self._empty_response()

        total_clues = await self.clue_repo.count_total()

        # --- 3-layer pipeline ---
        # Layer 1: Domain filter → Layer 2: Topic merge → Layer 3: Per-clue AI
        selected_clues = await self._select_clues(org_config.domains)

        if not selected_clues:
            result = self._build_result(org_config, total_clues, [], [])
            await cache_manager.set(cache_key, result, ttl=STALE_TTL)
            return result

        # Layer 3: Per-clue AI generation with concurrency limit
        raw_recommendations = await self._generate_per_clue(
            selected_clues, org_config.domains, org_config.style
        )

        # Sort recommendations by original clue score (descending)
        scored_recs = []
        for rec, clue in raw_recommendations:
            clue_score = getattr(clue, "_score", 0)
            scored_recs.append((clue_score, rec))
        scored_recs.sort(key=lambda x: x[0], reverse=True)

        recommendations = [
            {
                "id": f"rec{i+1}",
                "source": r.get("source", ""),
                "source_icon": r.get("source_icon", "newspaper"),
                "tag": r.get("tag", ""),
                "title": r.get("title", ""),
                "reason": r.get("reason", ""),
                "angles": r.get("angles", []),
            }
            for i, (_, r) in enumerate(scored_recs[:MAX_RECOMMENDATIONS])
        ]

        clue_ids = [str(c.id) for c in selected_clues]

        result = self._build_result(org_config, total_clues, clue_ids, recommendations)
        await cache_manager.set(cache_key, result, ttl=STALE_TTL)
        return result

    def _build_result(self, org_config, total_clues, clue_ids, recommendations) -> dict:
        return {
            "org_config": {
                "id": str(org_config.id),
                "name": org_config.name,
                "domains": org_config.domains,
                "style": org_config.style,
            },
            "total_clues": total_clues,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "clue_ids": clue_ids,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
        }

    # --- Layer 1 + 2: Select clues (domain filter + topic merge) ---

    async def _select_clues(self, domains: list[str]) -> list:
        """Layer 1: domain filter → Layer 2: topic merge → scored representative clues."""
        resolved_domains = set(resolve_domain(d) for d in domains)

        sources = await self.ds_repo.get_all_active()

        hotlist_ids = [s.id for s in sources if s.type in (DataSourceType.HOTLIST, DataSourceType.VIDEO)]
        account_ids = [s.id for s in sources if s.type == DataSourceType.ACCOUNT]
        source_map = {str(s.id): s for s in sources}

        # Fetch candidate pools per stratum, annotate with source metadata + classify domains
        hotlist_pool = []
        account_pool = []

        if hotlist_ids:
            hot_by_source = await self.clue_repo.get_hot_by_sources(hotlist_ids, limit=HOTLIST_PER_SOURCE)
            for sid, clues in hot_by_source.items():
                src = source_map.get(sid)
                for clue in clues:
                    self._annotate_clue(clue, src)
                hotlist_pool.extend(clues)

        if account_ids:
            latest_by_source = await self.clue_repo.get_latest_by_sources(account_ids, limit=ACCOUNT_PER_SOURCE)
            for sid, clues in latest_by_source.items():
                src = source_map.get(sid)
                for clue in clues:
                    self._annotate_clue(clue, src)
                account_pool.extend(clues)

        # --- Layer 1: Domain filter ---
        hotlist_filtered = self._filter_by_domains(hotlist_pool, resolved_domains)
        account_filtered = self._filter_by_domains(account_pool, resolved_domains)

        if len(hotlist_filtered) + len(account_filtered) < MIN_FILTERED_POOL:
            logger.info("discovery_domain_filter_fallback")
            hotlist_filtered = hotlist_pool
            account_filtered = account_pool

        now = datetime.now(timezone.utc)

        # Score within each stratum (scores stored on clue for later sorting)
        hotlist_scored = self._score_pool(hotlist_filtered, source_map, resolved_domains, now)
        account_scored = self._score_pool(account_filtered, source_map, resolved_domains, now)

        # --- Layer 2: Merge similar topics ---
        hotlist_merged = self._merge_similar_topics(hotlist_scored)
        account_merged = self._merge_similar_topics(account_scored)

        # Take quota from each stratum, sorted by score
        hotlist_selected = sorted(hotlist_merged, key=lambda c: c._score, reverse=True)[:HOTLIST_QUOTA]
        account_selected = sorted(account_merged, key=lambda c: c._score, reverse=True)[:ACCOUNT_QUOTA]

        return hotlist_selected + account_selected

    def _annotate_clue(self, clue, source: Optional):
        """Attach source metadata + classified domains as temp attributes."""
        platform_raw = source.platform if source else None
        if not platform_raw and source and source.config:
            platform_raw = source.config.get("platform")
        clue._platform_label = PLATFORM_LABELS.get(platform_raw, platform_raw or "未知")
        type_raw = source.type.value if source else "custom"
        type_map = {"hotlist": "热榜", "account": "KOL", "video": "热门视频", "custom": "自定义"}
        clue._source_type_label = type_map.get(type_raw, type_raw)
        clue._source_priority = source.priority if source else 5
        clue._classified_domains = classify_domains(clue.title, clue.tags)

    def _filter_by_domains(self, pool: list, resolved_domains: set) -> list:
        """Layer 1: keep only clues whose classified domains overlap with OrgConfig domains."""
        if not resolved_domains:
            return pool
        filtered = []
        for clue in pool:
            classified = getattr(clue, "_classified_domains", [])
            if classified and any(d in resolved_domains for d in classified):
                filtered.append(clue)
        return filtered

    def _score_pool(self, pool: list, source_map: dict, resolved_domains: set, now: datetime) -> list:
        """Compute and attach score to each clue in pool."""
        for clue in pool:
            source = source_map.get(str(clue.source_id))
            clue._score = self._compute_score(clue, source, resolved_domains, now)
        return pool

    def _compute_score(
        self,
        clue,
        source: Optional,
        resolved_domains: set,
        now: datetime,
    ) -> float:
        """score = w1*freshness + w2*spread + w3*authority + w4*domain_relevance"""
        hours_ago = max((now - clue.collected_at).total_seconds() / 3600, 0)
        freshness = math.exp(-hours_ago / 24)

        engagement = (clue.likes or 0) + (clue.comments or 0) + (clue.shares or 0)
        heat = parse_heat_value(clue.heat_value)
        heat_norm = math.log10(heat) / 8 if heat > 0 else 0.0
        eng_norm = math.log10(engagement) / 5 if engagement > 0 else 0.0
        spread = max(heat_norm, eng_norm)

        authority = (source.priority if source else 5) / 10

        classified = getattr(clue, "_classified_domains", [])
        if classified and resolved_domains:
            domain_relevance = sum(1 for d in classified if d in resolved_domains) / max(len(resolved_domains), 1)
        else:
            domain_relevance = 0.0

        return (
            W_FRESHNESS * freshness
            + W_SPREAD * spread
            + W_AUTHORITY * authority
            + W_DOMAIN_RELEVANCE * domain_relevance
        )

    # --- Layer 2: Merge similar topics ---

    def _merge_similar_topics(self, pool: list) -> list:
        """Merge clues about the same topic, keeping highest-scored representative.

        Two clues are "same topic" if their titles share a contiguous substring
        of length >= SIMILAR_TITLE_MIN_LEN (4 chars for Chinese text).
        """
        # Sort by score descending — first encounter is the representative
        sorted_pool = sorted(pool, key=lambda c: c._score, reverse=True)

        merged = []
        consumed = set()

        for i, rep in enumerate(sorted_pool):
            if id(rep) in consumed:
                continue
            group = [rep]

            for j, other in enumerate(sorted_pool):
                if j <= i or id(other) in consumed:
                    continue
                if self._titles_similar(rep.title, other.title):
                    group.append(other)
                    consumed.add(id(other))

            # Attach merge metadata to representative
            rep._merged_count = len(group)
            rep._merged_platforms = [getattr(c, "_platform_label", "未知") for c in group]
            unique_platforms = sorted(set(rep._merged_platforms))
            rep._merged_platforms_summary = f"来自{', '.join(unique_platforms)}等平台，共{len(group)}条相关线索"

            merged.append(rep)

        return merged

    def _titles_similar(self, title_a: str, title_b: str) -> bool:
        """Check if two titles share a significant common substring."""
        min_len = SIMILAR_TITLE_MIN_LEN
        if len(title_a) < min_len or len(title_b) < min_len:
            return False
        for i in range(len(title_a) - min_len + 1):
            if title_a[i:i + min_len] in title_b:
                return True
        return False

    # --- Layer 3: Per-clue AI generation ---

    async def _generate_per_clue(
        self,
        clues: list,
        domains: list[str],
        style: list[str],
    ) -> list[tuple]:
        """Call Qwen per clue, return (recommendation_dict, clue) pairs."""
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_AI_CALLS)

        async def _call_one(clue):
            async with semaphore:
                clue_text = self._format_single_clue_text(clue)
                try:
                    rec = await self.ai_service.generate_single_recommendation(
                        domains=domains,
                        style=style,
                        clue_text=clue_text,
                        clue_id=str(clue.id),
                    )
                    return (rec, clue)
                except Exception as e:
                    logger.warning("discovery_per_clue_failed", clue_id=str(clue.id), error=str(e))
                    return (None, clue)

        results = await asyncio.gather(*[_call_one(c) for c in clues])

        # Filter out failures
        return [(rec, clue) for rec, clue in results if rec is not None]

    def _format_single_clue_text(self, clue) -> str:
        """Format one clue with enriched metadata + merge info for single-clue prompt."""
        platform = getattr(clue, "_platform_label", "")
        source_type = getattr(clue, "_source_type_label", "")
        source_priority = getattr(clue, "_source_priority", 5)
        classified = getattr(clue, "_classified_domains", [])

        heat_str = clue.heat_value or "N/A"
        author = clue.author or "未知"

        engagement_str = ""
        likes = clue.likes or 0
        comments = clue.comments or 0
        shares = clue.shares or 0
        if likes or comments or shares:
            engagement_str = f" | 互动: {likes}赞+{comments}评+{shares}转"

        domain_str = ""
        if classified:
            domain_str = f" | 领域: {', '.join(classified)}"

        prefix = f"[{platform}·{source_type}]" if platform and source_type else "[未知]"

        line = f"{prefix} {clue.title} | 作者: {author} | 热度: {heat_str}{engagement_str} | 优先级: {source_priority}/10{domain_str}"

        # Append merge metadata if this clue represents multiple similar clues
        merge_summary = getattr(clue, "_merged_platforms_summary", None)
        if merge_summary:
            line += f"\n（该主题{merge_summary}）"

        return line

    # --- Helpers unchanged ---

    def _schedule_refresh(self) -> None:
        asyncio.ensure_future(self._background_refresh())

    async def _background_refresh(self) -> None:
        async with db_manager.session() as session:
            service = DiscoveryService(session)
            try:
                logger.info("discovery_background_refresh_start")
                await service._generate_and_cache()
                logger.info("discovery_background_refresh_done")
            except Exception as e:
                logger.error("discovery_background_refresh_error", error=str(e))

    def _empty_response(self) -> dict:
        return {
            "org_config": {"id": "", "name": "", "domains": [], "style": []},
            "total_clues": 0,
            "last_updated": "",
            "clue_ids": [],
            "recommendations": [],
            "total_recommendations": 0,
        }