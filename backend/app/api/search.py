from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Message, ResearchSession, Source, User
from app.core.config import settings
from app.services.web_search import DuckDuckGoHTMLSearchClient, RateLimitError

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/sessions/{session_id}", status_code=201)
async def search_and_attach_sources(
    session_id: int,
    query: str,
    max_results: int = 5,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Run a web search and attach results as Sources to a session.

    This is the MVP pipeline for F3. It stores sources and appends an assistant
    message summarizing what happened.
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

    client = DuckDuckGoHTMLSearchClient(
        cache_ttl_seconds=settings.search_cache_ttl_seconds,
        cache_max_items=settings.search_cache_max_items,
        rate_per_minute=settings.search_rate_per_minute,
    )
    try:
        results = await client.search(query, max_results=max_results)
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="Search failed") from exc

    created = 0
    for r in results:
        # De-dupe on URL within session
        existing = await db.execute(
            select(Source).where(Source.session_id == session.id, Source.url == r.url)
        )
        if existing.scalar_one_or_none():
            continue
        db.add(
            Source(
                session_id=session.id,
                title=r.title,
                url=r.url,
                snippet=r.snippet,
                confidence=None,
                fetched_at=datetime.utcnow(),
            )
        )
        created += 1

    if created:
        db.add(
            Message(
                session_id=session.id,
                role="assistant",
                content=f"Added {created} sources from web search: '{query}'.",
            )
        )
        session.status = "sourced"

    await db.commit()

    return {"added": created, "found": len(results)}
