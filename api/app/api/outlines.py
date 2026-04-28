"""Outlines API router"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.outlines_service import OutlinesService
from app.schemas.outlines import (
    OutlineListResponse,
    OutlineResponse,
    OutlineCreateRequest,
    OutlineUpdateRequest,
    OutlineGenerateRequest,
    OutlineRegenerateRequest,
)
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/api/outlines", tags=["outlines"])


@router.get("", response_model=OutlineListResponse)
async def list_outlines(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    return await service.list_outlines(page, page_size)


@router.get("/{outline_id}", response_model=OutlineResponse)
async def get_outline(
    outline_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    result = await service.get_outline(outline_id)
    if not result:
        raise NotFoundException("Outline not found")
    return result


@router.post("", response_model=OutlineResponse)
async def create_outline(
    request: OutlineCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    return await service.create_outline(
        title=request.title,
        summary=request.summary,
        urgency=request.urgency,
        user_id=UUID(current_user["id"]),
    )


@router.put("/{outline_id}", response_model=OutlineResponse)
async def update_outline(
    outline_id: UUID,
    request: OutlineUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    result = await service.update_outline(outline_id, **request.model_dump(exclude_none=True))
    if not result:
        raise NotFoundException("Outline not found")
    return result


@router.delete("/{outline_id}")
async def delete_outline(
    outline_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    deleted = await service.delete_outline(outline_id)
    if not deleted:
        raise NotFoundException("Outline not found")
    return {"detail": "Deleted"}


@router.post("/generate", response_model=OutlineResponse)
async def generate_outline(
    request: OutlineGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    return await service.generate_from_clues(
        clue_ids=request.clue_ids,
        additional_context=request.additional_context,
        user_id=UUID(current_user["id"]),
    )


@router.post("/{outline_id}/regenerate", response_model=OutlineResponse)
async def regenerate_section(
    outline_id: UUID,
    request: OutlineRegenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    result = await service.regenerate_section(outline_id, request.section)
    if not result:
        raise NotFoundException("Outline not found")
    return result