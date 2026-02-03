from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response

from app.core.config import settings
import uuid
from datetime import datetime

from app.services.infographic import InfographicRenderer
from app.services.jobs import Job
from app.services.research_worker import run_research_and_render
from app.services.storage import LocalMediaStorage
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Infographic, Message, ResearchSession, Source, User
from app.schemas.sessions import (
    InfographicOut,
    ResearchSessionCreate,
    ResearchSessionDetail,
    ResearchSessionOut,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{session_id}/export.json")
async def export_session_json(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Export a full research session as JSON.

    Includes: session metadata, sources, messages, and infographic metadata.
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

    await db.refresh(session, attribute_names=["sources", "messages", "infographic"])

    return {
        "session": {
            "id": session.id,
            "prompt": session.prompt,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
        },
        "sources": [
            {
                "id": src.id,
                "title": src.title,
                "url": src.url,
                "snippet": src.snippet,
                "fetched_at": (src.fetched_at.isoformat() if src.fetched_at else None),
                "confidence": src.confidence,
            }
            for src in session.sources
        ],
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in session.messages
        ],
        "infographic": (
            {
                "id": session.infographic.id,
                "image_url": session.infographic.image_url,
                "layout_meta": session.infographic.layout_meta,
                "claims": session.infographic.layout_meta.get("claims", []),
                "created_at": session.infographic.created_at.isoformat(),
            }
            if session.infographic
            else None
        ),
    }


@router.get("/{session_id}/infographic.svg")
async def export_infographic_svg(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export the session infographic as an SVG file."""
    res = await db.execute(
        select(ResearchSession).where(
            ResearchSession.id == session_id,
            ResearchSession.user_id == user.id,
        )
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.refresh(session, attribute_names=["infographic"])
    if not session.infographic or not session.infographic.image_url:
        raise HTTPException(status_code=404, detail="Infographic not found")

    image_url: str = session.infographic.image_url

    # If stored as a local media URL, read it from disk.
    #
    # Our MVP storage writes to settings.media_root and returns a URL under
    # settings.media_base_url (often http://localhost:8000/media). During tests
    # there's no external server to fetch from, so we map back to disk.
    if image_url.startswith(settings.media_base_url.rstrip("/") + "/"):
        rel = image_url[len(settings.media_base_url.rstrip("/")) + 1 :]
        try:
            storage = LocalMediaStorage(settings.media_root, settings.media_base_url)
            path = storage.resolve(rel)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))

        try:
            svg = path.read_bytes()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Infographic file missing")

        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": f"attachment; filename=infographic-session-{session.id}.svg"
            },
        )

    # Otherwise if it's an http(s) URL (e.g. remote object storage), redirect.
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return Response(status_code=307, headers={"Location": image_url})

    # Backward compatibility: handle legacy data URLs.
    if not image_url.startswith("data:image/svg+xml"):
        raise HTTPException(status_code=409, detail="Infographic is not an SVG")

    idx = image_url.find(",")
    if idx == -1:
        raise HTTPException(status_code=500, detail="Invalid infographic data URL")

    svg = image_url[idx + 1 :]

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Content-Disposition": f"attachment; filename=infographic-session-{session.id}.svg"
        },
    )


@router.post(
    "/{session_id}/run",
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_session_async(
    session_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Kick off an async research + render job for a session."""
    res = await db.execute(
        select(ResearchSession).where(
            ResearchSession.id == session_id,
            ResearchSession.user_id == user.id,
        )
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Mark session running
    session.status = "running"
    await db.commit()

    job_id = uuid.uuid4().hex

    queue = getattr(request.app.state, "job_queue", None)
    if queue is None:
        raise HTTPException(status_code=500, detail="Job queue not configured")

    async def _coro_factory() -> dict:
        # Use the same DB session dependency. For an in-process queue, this is ok.
        # For a real distributed worker, we'd open a fresh DB session.
        return await run_research_and_render(session_id=session_id, db=db)

    await queue.enqueue(
        job=Job(job_id=job_id, kind="research_and_render", created_at=datetime.utcnow()),
        coro_factory=_coro_factory,
    )

    return {"job_id": job_id, "session_id": session_id}


@router.post(
    "/{session_id}/infographic",
    response_model=InfographicOut,
    status_code=status.HTTP_201_CREATED,
)
async def generate_infographic(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and store a simple infographic for a session.

    Synchronous endpoint kept for backwards compatibility and fast iteration.
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

    await db.refresh(session, attribute_names=["sources", "infographic"])

    # Build minimal layout metadata with provenance.
    sources_meta = [
        {
            "source_id": s.id,
            "title": s.title,
            "url": s.url,
            "confidence": s.confidence,
        }
        for s in session.sources
    ]

    renderer = InfographicRenderer()
    rendered = renderer.render_session_infographic(prompt=session.prompt, sources=sources_meta)
    layout_meta = rendered.layout_meta
    svg = rendered.svg_bytes

    storage = LocalMediaStorage(settings.media_root, settings.media_base_url)
    stored = storage.save_bytes(
        rel_path=f"sessions/{session.id}/infographic.svg",
        content=svg,
    )
    image_url = stored.url

    if session.infographic:
        session.infographic.image_url = image_url
        session.infographic.layout_meta = layout_meta
    else:
        db.add(
            Infographic(
                session_id=session.id,
                image_url=image_url,
                layout_meta=layout_meta,
            )
        )

    session.status = "infographic_generated"
    await db.commit()

    # Return the stored infographic record.
    res2 = await db.execute(select(Infographic).where(Infographic.session_id == session.id))
    infographic = res2.scalar_one()
    return InfographicOut(
        id=infographic.id,
        image_url=infographic.image_url,
        layout_meta=infographic.layout_meta,
        created_at=infographic.created_at,
        claims=infographic.layout_meta.get("claims", []),
    )


@router.post("", response_model=ResearchSessionOut, status_code=201)
async def create_session(
    payload: ResearchSessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = ResearchSession(user_id=user.id, prompt=payload.prompt, status="created")
    db.add(session)

    # store initial user message
    db.add(Message(session=session, role="user", content=payload.prompt))
    await db.commit()
    await db.refresh(session)
    return ResearchSessionOut(
        id=session.id,
        prompt=session.prompt,
        status=session.status,
        created_at=session.created_at,
    )


@router.get("", response_model=list[ResearchSessionOut])
async def list_sessions(
    q: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ResearchSession).where(ResearchSession.user_id == user.id)
    if q:
        stmt = stmt.where(ResearchSession.prompt.ilike(f"%{q}%"))
    stmt = stmt.order_by(desc(ResearchSession.created_at)).limit(100)
    res = await db.execute(stmt)
    sessions = res.scalars().all()
    return [
        ResearchSessionOut(
            id=s.id,
            prompt=s.prompt,
            status=s.status,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=ResearchSessionDetail)
async def get_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ResearchSession).where(
            ResearchSession.id == session_id,
            ResearchSession.user_id == user.id,
        )
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load relationships explicitly (simple approach)
    await db.refresh(session, attribute_names=["sources", "messages", "infographic"])

    return ResearchSessionDetail(
        id=session.id,
        prompt=session.prompt,
        status=session.status,
        created_at=session.created_at,
        sources=[
            {
                "id": src.id,
                "title": src.title,
                "url": src.url,
                "snippet": src.snippet,
                "fetched_at": src.fetched_at,
                "confidence": src.confidence,
            }
            for src in session.sources
        ],
        messages=[
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in session.messages
        ],
        infographic=(
            {
                "id": session.infographic.id,
                "image_url": session.infographic.image_url,
                "layout_meta": session.infographic.layout_meta,
                "claims": session.infographic.layout_meta.get("claims", []),
                "created_at": session.infographic.created_at,
            }
            if session.infographic
            else None
        ),
    )


@router.post("/{session_id}/sources", status_code=201)
async def add_source(
    session_id: int,
    title: str,
    url: str,
    snippet: str | None = None,
    confidence: float | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ResearchSession).where(
            ResearchSession.id == session_id,
            ResearchSession.user_id == user.id,
        )
    )
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    src = Source(
        session_id=session.id,
        title=title,
        url=url,
        snippet=snippet,
        confidence=confidence,
        fetched_at=datetime.utcnow(),
    )
    db.add(src)
    await db.commit()
    return {"id": src.id}
