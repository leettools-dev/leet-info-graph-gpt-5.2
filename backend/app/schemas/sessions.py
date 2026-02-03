from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime


class SourceOut(BaseModel):
    id: int
    title: str
    url: str
    snippet: str | None = None
    fetched_at: datetime | None = None
    confidence: float | None = None


class InfographicOut(BaseModel):
    id: int
    image_url: str
    layout_meta: dict
    created_at: datetime


class ResearchSessionCreate(BaseModel):
    prompt: str


class ResearchSessionOut(BaseModel):
    id: int
    prompt: str
    status: str
    created_at: datetime


class ResearchSessionDetail(ResearchSessionOut):
    sources: list[SourceOut] = []
    messages: list[MessageOut] = []
    infographic: InfographicOut | None = None
