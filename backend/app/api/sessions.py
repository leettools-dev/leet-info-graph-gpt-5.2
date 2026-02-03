from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
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

    MVP implementation: creates a deterministic SVG based on session prompt and sources.
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

    title = (
        session.prompt.strip()[:80]
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    bullets = [
        f"{idx+1}. {s.title.strip()[:80]}"
        for idx, s in enumerate(session.sources[:5])
        if s.title
    ]
    if not bullets:
        bullets = ["Add sources to generate richer results."]

    layout_meta = {
        "title": title,
        "key_bullets": bullets,
        "sources": sources_meta,
        "generated_by": "mvp-svg-template",
        "version": 1,
    }

    # Render a basic SVG (stored as a data URL for now).
    lines = [
        "<svg xmlns='http://www.w3.org/2000/svg' width='800' height='450'>",
        "<rect width='100%' height='100%' fill='#0B1220'/>",
        "<text x='40' y='70' fill='#E5E7EB' font-family='Arial' font-size='28' font-weight='700'>",
        f"{title}",
        "</text>",
        "<text x='40' y='110' fill='#9CA3AF' font-family='Arial' font-size='14'>Generated infographic (MVP)</text>",
    ]
    y = 160
    for b in bullets[:8]:
        safe = (
            b.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        lines.append(
            f"<text x='60' y='{y}' fill='#E5E7EB' font-family='Arial' font-size='18'>{safe}</text>"
        )
        y += 36
    lines.append("</svg>")
    svg = "".join(lines)
    image_url = "data:image/svg+xml;utf8," + svg

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
