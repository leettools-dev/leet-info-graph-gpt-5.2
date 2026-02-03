from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Message, ResearchSession, Source, User
from app.schemas.sessions import (
    ResearchSessionCreate,
    ResearchSessionDetail,
    ResearchSessionOut,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


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
