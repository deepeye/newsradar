"""Dashboard response schemas"""
from typing import Optional, List

from app.schemas.common import CamelModel


class TrendingItem(CamelModel):
    id: str
    rank: int
    title: str
    heat_value: str
    status: Optional[str] = None
    url: Optional[str] = None


class PlatformTrendingCard(CamelModel):
    platform: str
    platform_label: str
    items: List[TrendingItem]
    last_updated: str


class KOLPost(CamelModel):
    id: str
    author: str
    verified: Optional[bool] = None
    content: str
    likes: int = 0
    shares: int = 0
    comments: int = 0
    time_ago: str = ""


class KOLColumn(CamelModel):
    platform: str
    platform_label: str
    posts: List[KOLPost]


class AISuggestion(CamelModel):
    id: str
    title: str
    description: str


class DashboardData(CamelModel):
    trending_cards: List[PlatformTrendingCard]
    kol_columns: List[KOLColumn]
    ai_suggestions: List[AISuggestion]
    active_threads: int = 0
    topic_alerts: int = 0
    quote: Optional[dict] = None