"""KOL API router"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
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

router = APIRouter(prefix="/api/kol", tags=["kol"])


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
