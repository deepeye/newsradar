"""KOL request/response schemas"""
from typing import List, Optional, Dict
from datetime import datetime

from app.schemas.common import CamelModel


class KOLCreate(CamelModel):
    platform: str  # "weibo" | "x"
    platform_id: str  # Weibo UID or X username
    screen_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    cookies: Optional[Dict[str, str]] = None


class KOLUpdate(CamelModel):
    screen_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None


class KOLResponse(CamelModel):
    id: str
    source_id: str
    platform: str
    platform_id: str
    screen_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    post_count: Optional[int] = None
    is_active: bool
    last_synced_at: Optional[datetime] = None
    cookie_status: Optional[Dict[str, int]] = None
    created_at: datetime
    updated_at: datetime


class KOLCookieImport(CamelModel):
    cookies: Dict[str, str]


class KOLPostResponse(CamelModel):
    id: str
    content: str
    url: Optional[str] = None
    author: Optional[str] = None
    likes: int = 0
    comments: int = 0
    shares: int = 0
    cover_image: Optional[str] = None
    collected_at: datetime


class KOLListResponse(CamelModel):
    total: int
    items: List[KOLResponse]


class KOLPostListResponse(CamelModel):
    total: int
    items: List[KOLPostResponse]
