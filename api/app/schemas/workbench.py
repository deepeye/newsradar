"""Workbench request/response schemas"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AISuggestionItem(BaseModel):
    id: str
    type: str
    original: str
    suggested: str
    reason: str


class ContentMetrics(BaseModel):
    objectivity: int = 0
    readability: str = ""


class ReferenceDoc(BaseModel):
    id: str
    title: str
    source: str
    last_updated: Optional[str] = None


class ArticleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    outline_id: Optional[str] = None
    target_word_count: int = 1600
    urgent: bool = False


class ArticleUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_word_count: Optional[int] = None
    urgent: Optional[bool] = None
    status: Optional[str] = None


class ArticleResponse(BaseModel):
    id: str
    outline_id: Optional[str] = None
    title: str
    author_id: Optional[str] = None
    content: Optional[str] = None
    word_count: int
    target_word_count: int
    completion_percent: int
    urgent: bool
    ai_suggestions: Optional[List[AISuggestionItem]] = None
    metrics: Optional[ContentMetrics] = None
    references: Optional[List[ReferenceDoc]] = None
    status: str
    last_saved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ArticleListResponse(BaseModel):
    total: int
    items: List[ArticleResponse]
