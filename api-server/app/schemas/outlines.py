"""Outlines request/response schemas"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class HeadlineSuggestion(BaseModel):
    style: str
    text: str


class OutlineItem(BaseModel):
    id: str
    content: str
    has_ai_rewrite: bool = False


class OutlineSection(BaseModel):
    id: str
    number: str
    title: str
    items: List[OutlineItem]


class InterviewDirection(BaseModel):
    id: str
    role: str
    description: str


class ReferenceLink(BaseModel):
    id: str
    title: str
    source: str
    url: Optional[str] = None


class OutlineGenerateRequest(BaseModel):
    clue_ids: List[str] = Field(..., min_length=1)
    additional_context: Optional[str] = None


class OutlineRegenerateRequest(BaseModel):
    section: str = Field(..., pattern="^(headlines|outline|interview)$")


class OutlineResponse(BaseModel):
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


class OutlineListResponse(BaseModel):
    total: int
    items: List[OutlineResponse]


class OutlineCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    summary: Optional[str] = None
    urgency: str = "中"


class OutlineUpdateRequest(BaseModel):
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
