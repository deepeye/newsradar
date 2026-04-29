"""Data source request/response schemas"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.schemas.common import CamelModel


class SourceGroupCreate(CamelModel):
    name: str
    collect_interval: int = 30
    is_active: bool = True


class SourceGroupUpdate(CamelModel):
    name: Optional[str] = None
    collect_interval: Optional[int] = None
    is_active: Optional[bool] = None


class SourceGroupResponse(CamelModel):
    id: str
    name: str
    collect_interval: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DataSourceCreate(CamelModel):
    group_id: str
    name: str
    type: str  # hotlist, account, video, custom
    collector_type: str = "configurable"  # configurable, plugin
    config: dict
    priority: int = 5
    is_active: bool = True


class DataSourceUpdate(CamelModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None


class DataSourceResponse(CamelModel):
    id: str
    group_id: str
    name: str
    type: str
    collector_type: str
    config: dict
    priority: int
    is_active: bool
    status: str
    last_collected_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    consecutive_failures: int = 0
    created_at: datetime
    updated_at: datetime


class SourceGroupListResponse(CamelModel):
    total: int
    items: List[SourceGroupResponse]


class DataSourceListResponse(CamelModel):
    total: int
    items: List[DataSourceResponse]