"""Dashboard API router"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.dashboard_service import DashboardService
from app.repositories.org_config_repo import OrgConfigRepository
from app.schemas.dashboard import DashboardData

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_config_repo = OrgConfigRepository(db)
    org_config = await org_config_repo.get_active()
    org_config_dict = None
    if org_config:
        org_config_dict = {
            "domains": org_config.domains,
            "style": org_config.style,
        }

    service = DashboardService(db)
    data = await service.get_dashboard_data(org_config_dict)
    return DashboardData(**data)