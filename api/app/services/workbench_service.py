"""Workbench service — article management and AI assistance"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.article_repo import ArticleRepository
from app.services.ai_service import AIService
from app.models.article import Article
from app.core.exceptions import NotFoundException
import structlog

logger = structlog.get_logger("workbench_service")


class WorkbenchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.article_repo = ArticleRepository(db)
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