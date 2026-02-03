import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_and_list_sessions_unauthenticated():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r = await ac.get("/api/sessions")
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_create_and_get_session_authenticated(tmp_path, monkeypatch):
    # Use temp sqlite db
    monkeypatch.setenv(
        "INFOGRAPH_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/test.db"
    )

    # re-import app with patched settings by creating a new instance
    from importlib import reload

    import app.core.config as config

    reload(config)

    import app.db.session as session

    reload(session)

    import app.main as main

    reload(main)

    async with AsyncClient(
        transport=ASGITransport(app=main.app), base_url="http://test"
    ) as ac:
        # dev login sets cookie via redirect
        r = await ac.get(
            "/api/auth/dev/login",
            params={"email": "a@example.com"},
            follow_redirects=False,
        )
        assert r.status_code in (302, 307)
        cookie = r.headers.get("set-cookie")
        assert cookie and "session=" in cookie

        # carry cookie
        ac.headers.update({"cookie": cookie.split(";", 1)[0]})

        r2 = await ac.post("/api/sessions", json={"prompt": "test prompt"})
        assert r2.status_code == 201
        sid = r2.json()["id"]

        r3 = await ac.get("/api/sessions")
        assert r3.status_code == 200
        assert len(r3.json()) == 1

        r4 = await ac.get(f"/api/sessions/{sid}")
        assert r4.status_code == 200
        detail = r4.json()
        assert detail["prompt"] == "test prompt"
        assert detail["messages"][0]["role"] == "user"

        # Generate infographic
        r5 = await ac.post(f"/api/sessions/{sid}/infographic")
        assert r5.status_code == 201
        info = r5.json()
        assert info["image_url"].startswith("data:image/svg+xml")
        assert info["layout_meta"]["title"]

        # Detail now includes infographic
        r6 = await ac.get(f"/api/sessions/{sid}")
        assert r6.status_code == 200
        detail2 = r6.json()
        assert detail2["infographic"] is not None
        assert detail2["infographic"]["image_url"].startswith("data:image/svg+xml")
