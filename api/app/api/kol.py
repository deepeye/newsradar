"""KOL API router"""
import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.kol_service import KOLService
from app.schemas.kol import (
    KOLCreate, KOLUpdate, KOLResponse,
    KOLListResponse, KOLCookieImport,
    KOLPostListResponse,
)
from app.core.exceptions import NotFoundException
from app.models.kol import KOLProfile
from app.models.clue import DataSource
from app.utils.cache import cache_manager

router = APIRouter(prefix="/api/kol", tags=["kol"])


@router.get("/cookies", response_model=list)
async def list_cookies(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all cookies grouped by platform"""
    service = KOLService(db)
    return await service.list_all_cookies()


@router.post("/cookies/import")
async def import_platform_cookies(
    request: KOLCookieImport,
    platform: str = Query(..., description="Platform: weibo or x"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import cookies for a platform (shared across all KOLs of that platform)"""
    service = KOLService(db)
    return await service.import_platform_cookies(platform, request.cookies)


@router.delete("/cookies/{cookie_id}")
async def delete_platform_cookie(
    cookie_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a platform-level cookie by ID"""
    service = KOLService(db)
    # Find any kol_id that has this cookie (for validation)
    deleted = await service.delete_cookie_by_id(cookie_id)
    if not deleted:
        raise NotFoundException("Cookie not found")
    return {"detail": "Deleted"}


@router.post("/collect")
async def collect_all_kols(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger collection for all active KOL data sources"""
    result = await db.execute(
        select(DataSource)
        .where(DataSource.collector_type == "kol")
        .where(DataSource.is_active == True)
    )
    sources = result.scalars().all()
    if not sources:
        return {"detail": "No active KOL sources", "count": 0}

    redis = cache_manager._client
    if not redis:
        return {"detail": "Redis not available", "count": 0}

    now = datetime.now(timezone.utc).isoformat()
    timestamp = datetime.now(timezone.utc).timestamp()
    count = 0
    for source in sources:
        config = source.config or {}
        task_data = json.dumps({
            "id": f"{source.id}_{timestamp}",
            "source_id": str(source.id),
            "priority": source.priority or 5,
            "retry_count": 0,
            "created_at": now,
            "metadata": {
                "collector_type": "kol",
                "source_type": "ACCOUNT",
                "config": config,
            },
        })
        score = 10 - (source.priority or 5)
        await redis.zadd("clue_collector:tasks", {task_data: score})
        count += 1

    return {"detail": f"Triggered {count} KOL sources", "count": count}


@router.get("", response_model=KOLListResponse)
async def list_kols(
    platform: str = Query(None, description="Filter by platform: weibo/x"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KOLService(db)
    return await service.list_kols(platform, page, page_size)


@router.post("", response_model=KOLResponse)
async def create_kol(
    request: KOLCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KOLService(db)
    return await service.create_kol(request)


@router.post("/{source_id}/collect")
async def collect_kol(
    source_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger collection for a single KOL data source"""
    result = await db.execute(
        select(DataSource).where(DataSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise NotFoundException("Data source not found")

    redis = cache_manager._client
    if not redis:
        return {"detail": "Redis not available", "count": 0}

    config = source.config or {}
    timestamp = datetime.now(timezone.utc).timestamp()
    task_data = json.dumps({
        "id": f"{source.id}_{timestamp}",
        "source_id": str(source.id),
        "priority": source.priority or 5,
        "retry_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "collector_type": "kol",
            "source_type": "ACCOUNT",
            "config": config,
        },
    })
    score = 10 - (source.priority or 5)
    await redis.zadd("clue_collector:tasks", {task_data: score})

    return {"detail": f"Triggered {source.name}", "count": 1}


@router.get("/{kol_id}", response_model=KOLResponse)
async def get_kol(
    kol_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KOLService(db)
    return await service.get_kol(kol_id)


@router.patch("/{kol_id}", response_model=KOLResponse)
async def update_kol(
    kol_id: UUID,
    request: KOLUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KOLService(db)
    return await service.update_kol(kol_id, request)


@router.delete("/{kol_id}")
async def delete_kol(
    kol_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KOLService(db)
    await service.delete_kol(kol_id)
    return {"detail": "Deleted"}


@router.post("/{kol_id}/cookies")
async def import_cookies(
    kol_id: UUID,
    request: KOLCookieImport,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KOLService(db)
    return await service.import_cookies(kol_id, request.cookies)


@router.delete("/{kol_id}/cookies/{cookie_id}")
async def delete_cookie(
    kol_id: UUID,
    cookie_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KOLService(db)
    deleted = await service.delete_cookie(kol_id, cookie_id)
    if not deleted:
        raise NotFoundException("Cookie not found")
    return {"detail": "Deleted"}


@router.get("/{kol_id}/posts", response_model=KOLPostListResponse)
async def list_kol_posts(
    kol_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KOLService(db)
    return await service.list_posts(kol_id, page, page_size)
