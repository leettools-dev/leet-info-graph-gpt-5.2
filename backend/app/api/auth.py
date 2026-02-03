from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.services.auth import create_session_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login")
async def google_login() -> dict:
    if not settings.google_client_id:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
    # Stub: frontend should redirect user to Google auth. For now we just expose config.
    return {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "scope": "openid email profile",
        "response_type": "code",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
    }


@router.get("/dev/login")
async def dev_login(email: str, db: AsyncSession = Depends(get_db)):
    # Development-only login helper.
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user:
        user = User(email=email, name=email.split("@")[0])
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_session_token(user.id)
    response = RedirectResponse(url=settings.frontend_origin + "/")
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 7,
    )
    return response
