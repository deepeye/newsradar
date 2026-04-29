"""Data sources API router"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.data_source_service import DataSourceService
from app.schemas.data_source import (
    SourceGroupListResponse,
    SourceGroupResponse,
    SourceGroupCreate,
    SourceGroupUpdate,
    DataSourceListResponse,
    DataSourceResponse,
    DataSourceCreate,
    DataSourceUpdate,
)
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/api/data-sources", tags=["data-sources"])


# ==================== Source Group Endpoints ====================

@router.get("/groups", response_model=SourceGroupListResponse)
async def list_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all source groups"""
    service = DataSourceService(db)
    return await service.list_groups(page, page_size)


@router.post("/groups", response_model=SourceGroupResponse)
async def create_group(
    request: SourceGroupCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new source group"""
    service = DataSourceService(db)
    return await service.create_group(request)


@router.get("/groups/{group_id}", response_model=SourceGroupResponse)
async def get_group(
    group_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a source group by ID"""
    service = DataSourceService(db)
    return await service.get_group(group_id)


@router.put("/groups/{group_id}", response_model=SourceGroupResponse)
async def update_group(
    group_id: UUID,
    request: SourceGroupUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a source group"""
    service = DataSourceService(db)
    return await service.update_group(group_id, request)


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a source group"""
    service = DataSourceService(db)
    await service.delete_group(group_id)
    return {"detail": "Deleted"}


# ==================== Data Source Endpoints ====================

@router.get("", response_model=DataSourceListResponse)
async def list_sources(
    group_id: UUID = Query(None, description="Filter by group ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List data sources"""
    service = DataSourceService(db)
    return await service.list_sources(group_id, page, page_size)


@router.post("", response_model=DataSourceResponse)
async def create_source(
    request: DataSourceCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new data source"""
    service = DataSourceService(db)
    return await service.create_source(request)


@router.get("/{source_id}", response_model=DataSourceResponse)
async def get_source(
    source_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a data source by ID"""
    service = DataSourceService(db)
    return await service.get_source(source_id)


@router.put("/{source_id}", response_model=DataSourceResponse)
async def update_source(
    source_id: UUID,
    request: DataSourceUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a data source"""
    service = DataSourceService(db)
    return await service.update_source(source_id, request)


@router.delete("/{source_id}")
async def delete_source(
    source_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a data source"""
    service = DataSourceService(db)
    await service.delete_source(source_id)
    return {"detail": "Deleted"}


@router.post("/{source_id}/toggle", response_model=DataSourceResponse)
async def toggle_source(
    source_id: UUID,
    is_active: bool = Query(True, description="Enable or disable"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle data source active status"""
    service = DataSourceService(db)
    return await service.toggle_source(source_id, is_active)