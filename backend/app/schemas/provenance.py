from __future__ import annotations

from pydantic import BaseModel, Field


class ClaimOut(BaseModel):
    """A claim that appears in an infographic with traceable provenance."""

    id: str = Field(..., description="Stable claim id within the session")
    text: str = Field(..., description="The claim text")
    source_ids: list[int] = Field(
        default_factory=list,
        description="IDs of Source records supporting this claim",
    )
