"""Outlines request/response schemas"""
from typing import List, Optional
from pydantic import Field
from datetime import datetime

from app.schemas.common import CamelModel


class HeadlineSuggestion(CamelModel):
    id: Optional[str] = None
    style: str
    text: str


class OutlineItem(CamelModel):
    id: Optional[str] = None
    content: str
    has_ai_rewrite: bool = False


class OutlineSection(CamelModel):
    id: Optional[str] = None
    number: str
    title: str
    items: List[OutlineItem]

    class Config:
        coerced_types = True

    def __init__(self, **data):
        if "number" in data and not isinstance(data["number"], str):
            data["number"] = str(data["number"])
        super().__init__(**data)


class InterviewDirection(CamelModel):
    id: Optional[str] = None
    role: str
    description: str


class ReferenceLink(CamelModel):
    id: Optional[str] = None
    title: str
    source: str
    url: Optional[str] = None


class OutlineGenerateRequest(CamelModel):
    clue_ids: List[str] = Field(..., min_length=1)
    additional_context: Optional[str] = None


class OutlineRegenerateRequest(CamelModel):
    section: str = Field(..., pattern="^(headlines|outline|interview)$")


class OutlineResponse(CamelModel):
    id: str
    title: str
    summary: Optional[str] = None
    urgency: str
    info_density: int
    headlines: Optional[List[HeadlineSuggestion]] = None
    lead_paragraph: Optional[str] = None
    outline_sections: Optional[List[OutlineSection]] = None
    interview_directions: Optional[List[InterviewDirection]] = None
    references: Optional[List[ReferenceLink]] = None
    source_clue_ids: Optional[List[str]] = None
    ai_model: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class OutlineListResponse(CamelModel):
    total: int
    items: List[OutlineResponse]


class OutlineCreateRequest(CamelModel):
    title: str = Field(..., min_length=1, max_length=500)
    summary: Optional[str] = None
    urgency: str = "中"


class OutlineUpdateRequest(CamelModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    urgency: Optional[str] = None
    info_density: Optional[int] = None
    headlines: Optional[List[HeadlineSuggestion]] = None
    lead_paragraph: Optional[str] = None
    outline_sections: Optional[List[OutlineSection]] = None
    interview_directions: Optional[List[InterviewDirection]] = None
    references: Optional[List[ReferenceLink]] = None
    status: Optional[str] = None