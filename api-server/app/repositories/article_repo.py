"""Article repository"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, ArticleStatus
from app.repositories.base import BaseRepository


class ArticleRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Article)

    async def create(
        self,
        title: str,
        author_id: Optional[UUID] = None,
        outline_id: Optional[UUID] = None,
        target_word_count: int = 1600,
        urgent: bool = False,
    ) -> Article:
        article = Article(
            title=title,
            author_id=author_id,
            outline_id=outline_id,
            target_word_count=target_word_count,
            urgent=urgent,
            status=ArticleStatus.DRAFT,
            content="",
            word_count=0,
        )
        self.session.add(article)
        await self.session.flush()
        return article

    async def save(
        self,
        article_id: UUID,
        title: Optional[str] = None,
        content: Optional[str] = None,
        **kwargs,
    ) -> Optional[Article]:
        article = await self.get_by_id(article_id)
        if not article:
            return None

        if title is not None:
            article.title = title
        if content is not None:
            article.content = content
            article.word_count = len(content)
        for key, value in kwargs.items():
            if hasattr(article, key) and value is not None:
                setattr(article, key, value)

        article.last_saved_at = datetime.now(timezone.utc)
        await self.session.flush()
        return article
