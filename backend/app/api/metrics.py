from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ResearchSession, User

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/adoption")
async def adoption_metrics(
    days: int = 30,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Compute simple adoption metrics for the calling user.

    MVP definition:
    - users_with_2plus_sessions: users who created >=2 sessions in window
    - eligible_users: users who created >=1 session in window
    - adoption_rate: users_with_2plus_sessions / eligible_users

    Today we only expose metrics for the authenticated user for simplicity.
    """

    # Clamp days to avoid unbounded queries.
    days = max(1, min(int(days), 365))
    window_start = datetime.utcnow() - timedelta(days=days)

    stmt: Select = (
        select(func.count(ResearchSession.id))
        .where(ResearchSession.user_id == user.id)
        .where(ResearchSession.created_at >= window_start)
    )
    res = await db.execute(stmt)
    sessions_in_window = int(res.scalar_one() or 0)

    eligible_users = 1 if sessions_in_window >= 1 else 0
    users_with_2plus_sessions = 1 if sessions_in_window >= 2 else 0

    adoption_rate = (
        (users_with_2plus_sessions / eligible_users) if eligible_users else 0.0
    )

    return {
        "window_days": days,
        "user_id": user.id,
        "sessions_in_window": sessions_in_window,
        "eligible_users": eligible_users,
        "users_with_2plus_sessions": users_with_2plus_sessions,
        "adoption_rate": adoption_rate,
    }
