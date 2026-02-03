from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, HttpUrl, field_validator


class SourceCreate(BaseModel):
    title: str
    url: HttpUrl
    snippet: str | None = None
    confidence: float | None = None

    @field_validator("title")
    @classmethod
    def _title_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title cannot be empty")
        if len(v.strip()) > 500:
            raise ValueError("title too long")
        return v.strip()


class SourceOut(BaseModel):
    id: int
    title: str
    url: str
    snippet: str | None = None
    fetched_at: datetime | None = None
    confidence: float | None = None
    score: float | None = None
