from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class GoogleOAuthError(RuntimeError):
    pass


async def exchange_code_for_userinfo(*, code: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange an OAuth authorization code for tokens, then fetch userinfo.

    Uses Google's token endpoint + OpenID Connect userinfo endpoint.
    """

    if not settings.google_client_id or not settings.google_client_secret:
        raise GoogleOAuthError("Google OAuth not configured")

    async with httpx.AsyncClient(timeout=20) as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_resp.status_code >= 400:
            raise GoogleOAuthError(
                f"token exchange failed ({token_resp.status_code}): {token_resp.text}"
            )

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise GoogleOAuthError("token exchange response missing access_token")

        userinfo_resp = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code >= 400:
            raise GoogleOAuthError(
                f"userinfo fetch failed ({userinfo_resp.status_code}): {userinfo_resp.text}"
            )
        return userinfo_resp.json()
