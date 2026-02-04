from __future__ import annotations

from datetime import datetime
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Infographic, Message, ResearchSession, Source
from app.services.infographic import InfographicRenderer
from app.services.ingest import IngestPipeline
from app.services.storage import LocalMediaStorage
from app.services.web_search import DuckDuckGoHTMLSearchClient


async def run_research_and_render(*, session_id: int, db: AsyncSession) -> dict:
    """End-to-end research job: search -> ingest sources -> render infographic.

    Also returns timing metadata (milliseconds) to support latency SLO tracking.

    Persists Sources and an Infographic for the session.

    Returns a small result payload suitable for a job status endpoint.
    """

    t0 = perf_counter()

    res = await db.execute(select(ResearchSession).where(ResearchSession.id == session_id))
    session = res.scalar_one_or_none()
    if session is None:
        return {"session_id": session_id, "status": "missing"}

    query = session.prompt

    # 1) Web search
    t_search0 = perf_counter()
    search_client = DuckDuckGoHTMLSearchClient()
    hits = await search_client.search(query)
    t_search_ms = int((perf_counter() - t_search0) * 1000)

    # 2) Ingest a few sources (guardrails to avoid runaway cost/latency)
    t_ingest0 = perf_counter()
    pipeline = IngestPipeline(max_chars=settings.ingest_max_source_chars_for_summarization)
    ingested = []
    failures = 0
    for h in hits[: settings.search_max_results]:
        if len(ingested) >= settings.ingest_max_sources_per_session:
            break
        if failures >= settings.ingest_max_failures_per_session:
            break
        try:
            ing = await pipeline.ingest(h.url)
        except Exception:
            failures += 1
            continue
        ingested.append((h, ing))

    # 3) Persist sources + assistant message
    for h, ing in ingested:
        db.add(
            Source(
                session_id=session.id,
                title=ing.title or h.title,
                url=ing.url,
                snippet=ing.snippet or h.snippet,
                confidence=1.0,
                score=None,
                fetched_at=datetime.utcnow(),
            )
        )

    db.add(
        Message(
            session_id=session.id,
            role="assistant",
            content=f"Collected {len(ingested)} sources.",
        )
    )

    await db.commit()
    t_ingest_ms = int((perf_counter() - t_ingest0) * 1000)

    # 4) Render infographic based on persisted sources
    await db.refresh(session, attribute_names=["sources", "infographic"])

    sources_meta = [
        {
            "source_id": s.id,
            "title": s.title,
            "url": s.url,
            "confidence": s.confidence,
        }
        for s in session.sources
    ]

    t_render0 = perf_counter()
    renderer = InfographicRenderer()
    rendered = renderer.render_session_infographic(prompt=session.prompt, sources=sources_meta)
    t_render_ms = int((perf_counter() - t_render0) * 1000)

    storage = LocalMediaStorage(settings.media_root, settings.media_base_url)
    t_store0 = perf_counter()
    stored = storage.save_bytes(
        rel_path=f"sessions/{session.id}/infographic.svg",
        content=rendered.svg_bytes,
    )
    t_store_ms = int((perf_counter() - t_store0) * 1000)

    if session.infographic:
        session.infographic.image_url = stored.url
        session.infographic.layout_meta = rendered.layout_meta
    else:
        db.add(
            Infographic(
                session_id=session.id,
                image_url=stored.url,
                layout_meta=rendered.layout_meta,
            )
        )

    session.status = "completed"
    await db.commit()

    t_total_ms = int((perf_counter() - t0) * 1000)

    return {
        "session_id": session.id,
        "status": session.status,
        "sources_created": len(ingested),
        "infographic_url": stored.url,
        "timing_ms": {
            "total": t_total_ms,
            "search": t_search_ms,
            "ingest": t_ingest_ms,
            "render": t_render_ms,
            "store": t_store_ms,
        },
    }
