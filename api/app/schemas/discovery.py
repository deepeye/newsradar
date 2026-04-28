"""AI Discovery request/response schemas"""
from typing import List, Optional
from pydantic import BaseModel


class OrgConfigResponse(BaseModel):
    id: str
    name: str
    domains: List[str]
    style: List[str]


class OrgConfigUpdate(BaseModel):
    name: Optional[str] = None
    domains: Optional[List[str]] = None
    style: Optional[List[str]] = None


class AITopicRecommendation(BaseModel):
    id: str
    source: str
    source_icon: str
    tag: str
    title: str
    reason: str
    angles: List[str]


class DiscoveryResponse(BaseModel):
    org_config: OrgConfigResponse
    total_clues: int
    last_updated: str
    recommendations: List[AITopicRecommendation]
    total_recommendations: int
