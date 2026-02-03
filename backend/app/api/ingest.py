from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import Message, ResearchSession, Source, User
from app.services.ingest import IngestPipeline
from app.services.source_fetcher import FetchError, HTTPSourceFetcher
from app.services.web_search import SimpleTTLCache, TokenBucketRateLimiter

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/sessions/{session_id}", status_code=201)
async def ingest_sources_for_session(
    session_id: int,
    max_sources: int = 5,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Fetch + parse + summarize saved sources.

    MVP behavior:
    - processes up to `max_sources` sources that don't have a snippet yet
    - fills `Source.snippet` from fetched page summary
    """

    res = await db.execute(
        select(ResearchSession).where(
            ResearchSession.id == session_id,
            ResearchSession.user_id == user.id,
        )
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.refresh(session, attribute_names=["sources"])

    fetcher = HTTPSourceFetcher(
        cache=SimpleTTLCache(
            ttl_seconds=settings.fetch_cache_ttl_seconds,
            max_items=settings.fetch_cache_max_items,
        ),
        rate_limiter=TokenBucketRateLimiter(rate_per_minute=settings.fetch_rate_per_minute),
    )
    pipeline = IngestPipeline(fetcher=fetcher)

    processed = 0
    skipped = 0
    for src in session.sources:
        if processed >= max_sources:
            break
        if src.snippet:  # already ingested
            skipped += 1
            continue
        try:
            ingested = await pipeline.ingest(src.url)
        except FetchError:
            skipped += 1
            continue

        if ingested.title:
            src.title = ingested.title[:500]
        src.snippet = ingested.snippet
        src.fetched_at = datetime.utcnow()
        processed += 1

    if processed:
        db.add(
            Message(
                session_id=session.id,
                role="assistant",
                content=f"Ingested {processed} sources (fetched + summarized).",
            )
        )
        session.status = "ingested"

    await db.commit()
    return {"processed": processed, "skipped": skipped, "total": len(session.sources)}
