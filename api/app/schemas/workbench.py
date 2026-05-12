"""Workbench request/response schemas"""
from typing import List, Optional
from pydantic import Field
from datetime import datetime

from app.schemas.common import CamelModel


class AISuggestionItem(CamelModel):
    id: str
    type: str
    original: str
    suggested: str
    reason: str


class ContentMetrics(CamelModel):
    objectivity: int = 0
    readability: str = ""


class ReferenceDoc(CamelModel):
    id: str
    title: str
    source: str
    last_updated: Optional[str] = None


class ContinueWritingResponse(CamelModel):
    continued_content: str = ""
    section_title: str = ""


class SuggestRequest(CamelModel):
    title: str = Field(default="")
    content: str = Field(..., min_length=1)


class SuggestResponse(CamelModel):
    ai_suggestions: List[AISuggestionItem] = []


class TranslateRequest(CamelModel):
    target_language: str = Field(..., min_length=1)


class TranslateResponse(CamelModel):
    translated_content: str = ""
    target_language: str = ""


class FactClaim(CamelModel):
    claim: str
    type: str
    confidence: str
    search_query: str


class SearchEvidence(CamelModel):
    title: str
    snippet: str
    source: str
    url: str


class FactCheckResultItem(CamelModel):
    claim: str
    type: str
    confidence: str
    status: str
    evidence: str
    source_urls: List[str] = []


class FactCheckResponse(CamelModel):
    claims: List[FactClaim] = []
    search_results: List[SearchEvidence] = []
    results: List[FactCheckResultItem] = []


class ArticleCreateRequest(CamelModel):
    title: str = Field(..., min_length=1, max_length=500)
    outline_id: Optional[str] = None
    target_word_count: int = 1600
    urgent: bool = False


class GenerateArticleFromOutlineRequest(CamelModel):
    outline_id: str = Field(..., min_length=1)
    headline_index: Optional[int] = None


class ArticleUpdateRequest(CamelModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_word_count: Optional[int] = None
    urgent: Optional[bool] = None
    status: Optional[str] = None


class ArticleResponse(CamelModel):
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


class ArticleListResponse(CamelModel):
    total: int
    items: List[ArticleResponse]