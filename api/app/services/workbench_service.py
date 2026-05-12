"""Workbench service — article management and AI assistance"""
import json
from typing import Optional, AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.article_repo import ArticleRepository
from app.repositories.outline_repo import OutlineRepository
from app.repositories.org_config_repo import OrgConfigRepository
from app.services.ai_service import AIService
from app.models.article import Article
from app.models.outline import TopicOutline
from app.core.exceptions import NotFoundException
import structlog

logger = structlog.get_logger("workbench_service")


class WorkbenchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.article_repo = ArticleRepository(db)
        self.outline_repo = OutlineRepository(db)
        self.org_config_repo = OrgConfigRepository(db)
        self.ai_service = AIService()

    async def list_articles(self, page: int = 1, page_size: int = 20) -> dict:
        offset = (page - 1) * page_size
        items = await self.article_repo.get_all(limit=page_size, offset=offset)
        total = await self.article_repo.count()
        return {
            "total": total,
            "items": [self._format_article(a) for a in items],
        }

    async def get_article(self, article_id: UUID) -> Optional[dict]:
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            return None
        return self._format_article(article)

    async def create_article(
        self,
        title: str,
        author_id: Optional[UUID],
        outline_id: Optional[UUID],
        target_word_count: int,
        urgent: bool,
    ) -> dict:
        article = await self.article_repo.create(
            title=title,
            author_id=author_id,
            outline_id=outline_id,
            target_word_count=target_word_count,
            urgent=urgent,
        )
        return self._format_article(article)

    async def save_article(self, article_id: UUID, **kwargs) -> Optional[dict]:
        article = await self.article_repo.save(article_id, **kwargs)
        if not article:
            return None
        return self._format_article(article)

    async def delete_article(self, article_id: UUID) -> bool:
        return await self.article_repo.delete_by_id(article_id)

    async def generate_article_from_outline(
        self,
        outline_id: UUID,
        headline_index: Optional[int],
        author_id: Optional[UUID],
        target_word_count: int = 3000,
    ) -> dict:
        """Create article with AI-generated initial draft from outline."""
        outline = await self.outline_repo.get_by_id(outline_id)
        if not outline:
            raise NotFoundException(f"Outline {outline_id} not found")

        # Select title from headlines or fallback to outline title
        selected_title = outline.title
        if headline_index is not None and outline.headlines:
            headlines = outline.headlines
            if 0 <= headline_index < len(headlines):
                hl = headlines[headline_index]
                selected_title = hl.get("text", outline.title)

        lead_paragraph = outline.lead_paragraph or outline.summary or ""
        # Get style from OrgConfig
        org_config = await self.org_config_repo.get_active()
        style = org_config.style if org_config else []
        outline_sections = outline.outline_sections or []

        try:
            draft_result = await self.ai_service.generate_initial_draft(
                title=selected_title,
                style=style,
                lead_paragraph=lead_paragraph,
                outline_sections=outline_sections,
                outline_id=str(outline_id),
            )
            draft_content = draft_result.get("content", "")
        except Exception as e:
            logger.error("workbench_generate_draft_failed", error=str(e))
            draft_content = ""

        # Combine: title heading + lead paragraph + AI draft
        full_content = f"# {selected_title}\n\n{lead_paragraph}\n\n{draft_content}"

        article = await self.article_repo.create(
            title=selected_title,
            author_id=author_id,
            outline_id=outline_id,
            target_word_count=target_word_count,
            urgent=outline.urgency == "高",
        )
        # Save the generated draft content
        if full_content:
            article = await self.article_repo.save(article.id, content=full_content)
        return self._format_article(article)

    async def generate_article_from_outline_stream(
        self,
        outline_id: UUID,
        headline_index: Optional[int],
        author_id: Optional[UUID],
        target_word_count: int = 3000,
    ) -> AsyncGenerator[dict, None]:
        """Stream article generation: create first, then stream draft content."""
        outline = await self.outline_repo.get_by_id(outline_id)
        if not outline:
            raise NotFoundException(f"Outline {outline_id} not found")

        selected_title = outline.title
        if headline_index is not None and outline.headlines:
            if 0 <= headline_index < len(outline.headlines):
                hl = outline.headlines[headline_index]
                selected_title = hl.get("text", outline.title)

        lead_paragraph = outline.lead_paragraph or outline.summary or ""
        org_config = await self.org_config_repo.get_active()
        style = org_config.style if org_config else []
        outline_sections = outline.outline_sections or []

        # Create article first (empty content)
        article = await self.article_repo.create(
            title=selected_title,
            author_id=author_id,
            outline_id=outline_id,
            target_word_count=target_word_count,
            urgent=outline.urgency == "高",
        )
        # Flush so the article is visible to subsequent requests
        # before the SSE stream finishes (the request-level commit
        # only happens after StreamingResponse completes)
        await self.db.commit()

        yield {"event": "created", "data": {
            "articleId": str(article.id),
            "title": selected_title,
            "leadParagraph": lead_paragraph,
        }}

        # Stream AI draft content
        prefix = f"# {selected_title}\n\n{lead_paragraph}\n\n"
        accumulated = prefix

        try:
            async for chunk in self.ai_service.generate_initial_draft_stream(
                title=selected_title,
                style=style,
                lead_paragraph=lead_paragraph,
                outline_sections=outline_sections,
            ):
                accumulated += chunk
                yield {"event": "chunk", "data": {"content": chunk}}
        except Exception as e:
            logger.error("workbench_stream_draft_failed", error=str(e))
            yield {"event": "error", "data": {"error": str(e)}}

        # Save final content
        await self.article_repo.save(article.id, content=accumulated)
        final_article = await self.article_repo.get_by_id(article.id)
        yield {"event": "done", "data": self._format_article(final_article) if final_article else {}}

    async def ai_suggest_from_content(self, title: str, content: str) -> dict:
        try:
            suggestions = await self.ai_service.generate_writing_suggestions(
                title=title,
                content=content,
            )
            formatted = [
                {
                    "id": f"sug{i+1}",
                    "type": s.get("type", "style"),
                    "original": s.get("original", ""),
                    "suggested": s.get("suggested", ""),
                    "reason": s.get("reason", ""),
                }
                for i, s in enumerate(suggestions)
            ]
            return {"aiSuggestions": formatted}
        except Exception as e:
            logger.error("workbench_ai_suggest_from_content_failed", error=str(e))
            return {"aiSuggestions": []}

    async def ai_suggest(self, article_id: UUID) -> Optional[dict]:
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            return None

        try:
            suggestions = await self.ai_service.generate_writing_suggestions(
                title=article.title,
                content=article.content or "",
            )
            formatted = [
                {
                    "id": f"sug{i+1}",
                    "type": s.get("type", "style"),
                    "original": s.get("original", ""),
                    "suggested": s.get("suggested", ""),
                    "reason": s.get("reason", ""),
                }
                for i, s in enumerate(suggestions)
            ]
            # Save suggestions to article
            await self.article_repo.save(article_id, ai_suggestions=formatted)
            return {"ai_suggestions": formatted}
        except Exception as e:
            logger.error("workbench_ai_suggest_failed", error=str(e))
            return {"ai_suggestions": []}

    async def ai_metrics(self, article_id: UUID) -> Optional[dict]:
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            return None

        try:
            metrics = await self.ai_service.analyze_content_metrics(
                content=article.content or "",
            )
            formatted = {
                "objectivity": metrics.get("objectivity", 0),
                "readability": metrics.get("readability", ""),
            }
            await self.article_repo.save(article_id, metrics=formatted)
            return {"metrics": formatted}
        except Exception as e:
            logger.error("workbench_ai_metrics_failed", error=str(e))
            return {"metrics": {"objectivity": 0, "readability": ""}}

    async def ai_continue_writing(self, article_id: UUID) -> Optional[dict]:
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            return None

        outline_sections = []
        if article.outline_id:
            outline = await self.outline_repo.get_by_id(article.outline_id)
            if outline and outline.outline_sections:
                outline_sections = outline.outline_sections

        try:
            result = await self.ai_service.continue_writing(
                title=article.title,
                content=article.content or "",
                outline_sections=outline_sections,
            )
            section_title = result.get("section_title", "")
            continued_content = result.get("continued_content", "")

            if continued_content:
                separator = f"\n\n## {section_title}\n\n" if section_title else "\n\n"
                new_content = (article.content or "") + separator + continued_content
                await self.article_repo.save(article_id, content=new_content)
                return {"continued_content": continued_content, "section_title": section_title}
            return {"continued_content": "", "section_title": ""}
        except Exception as e:
            logger.error("workbench_ai_continue_failed", error=str(e))
            return {"continued_content": "", "section_title": ""}

    async def ai_translate(self, article_id: UUID, target_language: str) -> Optional[dict]:
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            return None

        try:
            result = await self.ai_service.translate(
                content=article.content or "",
                target_language=target_language,
            )
            translated_content = result.get("translated_content", "")
            return {"translated_content": translated_content, "target_language": target_language}
        except Exception as e:
            logger.error("workbench_ai_translate_failed", error=str(e))
            return {"translated_content": "", "target_language": target_language}

    async def ai_fact_check(self, article_id: UUID) -> Optional[dict]:
        """Hybrid fact-checking: claim extraction -> search -> synthesis."""
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            return None

        try:
            # Phase 1: Extract claims
            claims = await self.ai_service.extract_claims(
                title=article.title,
                content=article.content or "",
            )
            if not claims:
                return {"claims": [], "search_results": [], "results": []}

            # Phase 2: Cross-reference medium/low confidence claims via Google News
            search_claims = [c for c in claims if c.get("confidence") in ("medium", "low")]
            search_results = []

            if search_claims:
                import httpx
                from app.core.config import settings
                collector_url = settings.COLLECTOR_API_URL
                for claim in search_claims:
                    try:
                        async with httpx.AsyncClient(timeout=30) as client:
                            resp = await client.post(
                                f"{collector_url}/api/search/google-news",
                                json={"query": claim.get("search_query", claim.get("claim", "")), "max_results": 5},
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                if data.get("success"):
                                    search_results.extend(data.get("results", []))
                    except Exception as e:
                        logger.error("fact_check_search_failed", claim=claim.get("claim", ""), error=str(e))

            # Phase 3: Synthesize verification results
            results = await self.ai_service.synthesize_fact_check(claims, search_results)

            return {
                "claims": claims,
                "search_results": search_results,
                "results": results,
            }
        except Exception as e:
            logger.error("workbench_ai_fact_check_failed", error=str(e))
            return {"claims": [], "search_results": [], "results": []}

    def _format_article(self, article: Article) -> dict:
        completion = 0
        if article.target_word_count > 0:
            completion = min(int(article.word_count / article.target_word_count * 100), 100)

        return {
            "id": str(article.id),
            "outline_id": str(article.outline_id) if article.outline_id else None,
            "title": article.title,
            "author_id": str(article.author_id) if article.author_id else None,
            "content": article.content,
            "word_count": article.word_count,
            "target_word_count": article.target_word_count,
            "completion_percent": completion,
            "urgent": article.urgent,
            "ai_suggestions": article.ai_suggestions,
            "metrics": article.metrics,
            "references": article.references,
            "status": article.status,
            "last_saved_at": article.last_saved_at,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
        }