import pytest


@pytest.mark.asyncio
async def test_google_callback_sets_session_cookie(client, monkeypatch):
    """Ensure callback creates/updates user and sets our session cookie."""

    import app.api.auth as auth_router

    async def _fake_exchange_code_for_userinfo(*, code: str, redirect_uri: str):
        assert code == "abc"
        assert redirect_uri
        return {"email": "person@example.com", "name": "Person"}

    monkeypatch.setattr(
        auth_router,
        "exchange_code_for_userinfo",
        _fake_exchange_code_for_userinfo,
    )

    # Simulate browser: state is stored as a cookie and also returned as query param.
    login = await client.get("/api/auth/google/login")
    assert login.status_code == 200
    state = login.json()["state"]

    r = await client.get(
        "/api/auth/google/callback",
        params={"code": "abc", "state": state},
        follow_redirects=False,
    )

    assert r.status_code in (302, 307)
    cookie = r.headers.get("set-cookie")
    assert cookie and "session=" in cookie
