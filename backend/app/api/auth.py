from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.services.auth import create_session_token
from app.services.google_oauth import exchange_code_for_userinfo

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login")
async def google_login() -> dict:
    """Return Google OAuth authorization URL parameters.

    Frontend should redirect the user to `auth_url` with these query params.
    """
    if not settings.google_client_id:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    return {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "scope": "openid email profile",
        "response_type": "code",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "access_type": "offline",
        "prompt": "consent",
    }


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """OAuth callback.

    Exchanges `code` for tokens and fetches the user's profile (email/name). Creates or
    updates the local user record and sets our session cookie.

    Note: CSRF `state` validation should be added (tracked as a follow-up security task).
    """
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    try:
        userinfo = await exchange_code_for_userinfo(
            code=code,
            redirect_uri=settings.google_redirect_uri,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=401, detail=f"OAuth exchange failed: {e}")

    email = userinfo.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Google did not return an email")

    name = userinfo.get("name") or userinfo.get("given_name") or email.split("@")[0]

    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user:
        user = User(email=email, name=name)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif name and user.name != name:
        user.name = name
        await db.commit()

    token = create_session_token(user.id)

    response = RedirectResponse(url=settings.frontend_origin + "/")
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=60 * 60 * 24 * 7,
    )
    return response


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
        secure=settings.cookie_secure,
        max_age=60 * 60 * 24 * 7,
    )
    return response
