"""Workbench API router"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.workbench_service import WorkbenchService
from app.schemas.workbench import (
    ArticleListResponse,
    ArticleResponse,
    ArticleCreateRequest,
    ArticleUpdateRequest,
)
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/api/workbench", tags=["workbench"])


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    return await service.list_articles(page, page_size)


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    result = await service.get_article(article_id)
    if not result:
        raise NotFoundException("Article not found")
    return result


@router.post("/articles", response_model=ArticleResponse)
async def create_article(
    request: ArticleCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    return await service.create_article(
        title=request.title,
        author_id=UUID(current_user["id"]),
        outline_id=UUID(request.outline_id) if request.outline_id else None,
        target_word_count=request.target_word_count,
        urgent=request.urgent,
    )


@router.put("/articles/{article_id}", response_model=ArticleResponse)
async def save_article(
    article_id: UUID,
    request: ArticleUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    result = await service.save_article(
        article_id, **request.model_dump(exclude_none=True)
    )
    if not result:
        raise NotFoundException("Article not found")
    return result


@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    deleted = await service.delete_article(article_id)
    if not deleted:
        raise NotFoundException("Article not found")
    return {"detail": "Deleted"}


@router.post("/articles/{article_id}/ai-suggest")
async def ai_suggest(
    article_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    result = await service.ai_suggest(article_id)
    if result is None:
        raise NotFoundException("Article not found")
    return result


@router.post("/articles/{article_id}/ai-metrics")
async def ai_metrics(
    article_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    result = await service.ai_metrics(article_id)
    if result is None:
        raise NotFoundException("Article not found")
    return result