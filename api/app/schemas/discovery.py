"""AI Discovery request/response schemas"""
from typing import List, Optional

from app.schemas.common import CamelModel


class OrgConfigResponse(CamelModel):
    id: str
    name: str
    domains: List[str]
    style: List[str]


class OrgConfigUpdate(CamelModel):
    name: Optional[str] = None
    domains: Optional[List[str]] = None
    style: Optional[List[str]] = None


class AITopicRecommendation(CamelModel):
    id: str
    source: str
    source_icon: str
    tag: str
    title: str
    reason: str
    angles: List[str]


class DiscoveryResponse(CamelModel):
    org_config: OrgConfigResponse
    total_clues: int
    last_updated: str
    clue_ids: List[str]
    recommendations: List[AITopicRecommendation]
    total_recommendations: int