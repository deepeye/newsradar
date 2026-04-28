"""Discovery API router"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.discovery_service import DiscoveryService
from app.schemas.discovery import (
    DiscoveryResponse,
    OrgConfigResponse,
    OrgConfigUpdate,
)

router = APIRouter(prefix="/api/discovery", tags=["discovery"])


@router.get("/config", response_model=OrgConfigResponse)
async def get_config(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DiscoveryService(db)
    config = await service.get_config()
    if not config:
        return OrgConfigResponse(id="", name="", domains=[], style=[])
    return OrgConfigResponse(**config)


@router.put("/config", response_model=OrgConfigResponse)
async def update_config(
    request: OrgConfigUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DiscoveryService(db)
    config = await service.update_config(
        name=request.name,
        domains=request.domains,
        style=request.style,
    )
    return OrgConfigResponse(**config)


@router.get("", response_model=DiscoveryResponse)
async def get_discovery(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DiscoveryService(db)
    return await service.get_recommendations()


@router.post("/refresh", response_model=DiscoveryResponse)
async def refresh_discovery(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DiscoveryService(db)
    return await service.get_recommendations(force_refresh=True)