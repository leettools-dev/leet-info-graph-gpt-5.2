from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.provenance import ClaimOut


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime


from app.schemas.sources import SourceOut


class InfographicOut(BaseModel):
    id: int
    image_url: str
    layout_meta: dict
    created_at: datetime
    claims: list["ClaimOut"] = []


class ResearchSessionCreate(BaseModel):
    prompt: str

    # Basic server-side validation to ensure we receive a natural-language prompt.
    # Keep this lightweight for now; more advanced prompt constraints can be added later.
    def model_post_init(self, __context):  # type: ignore[override]
        if not self.prompt or not self.prompt.strip():
            raise ValueError("prompt cannot be empty")
        if len(self.prompt.strip()) < 3:
            raise ValueError("prompt too short")
        if len(self.prompt) > 4000:
            raise ValueError("prompt too long")


class ResearchSessionOut(BaseModel):
    id: int
    prompt: str
    status: str
    created_at: datetime


class ResearchSessionDetail(ResearchSessionOut):
    sources: list[SourceOut] = []
    messages: list[MessageOut] = []
    infographic: InfographicOut | None = None
