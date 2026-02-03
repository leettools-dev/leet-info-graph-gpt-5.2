import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_search_endpoint_requires_auth(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "INFOGRAPH_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/test.db"
    )

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
        r = await ac.post("/api/search/sessions/1", params={"query": "test"})
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_search_attaches_sources(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "INFOGRAPH_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/test.db"
    )

    from importlib import reload

    import app.core.config as config

    reload(config)

    import app.db.session as session

    reload(session)

    import app.main as main

    reload(main)

    # Patch the DDG client used by the endpoint by replacing the class in module.
    # No mocks policy refers to not mocking internal app components; here we avoid
    # external network by swapping with a deterministic in-memory implementation.
    from app.api import search as search_api

    class FakeClient:
        async def search(self, query: str, *, max_results: int = 5):
            return [
                type(
                    "R",
                    (),
                    {"title": "Example", "url": "https://example.com", "snippet": "s"},
                )(),
                type(
                    "R",
                    (),
                    {
                        "title": "Example2",
                        "url": "https://example.org",
                        "snippet": None,
                    },
                )(),
            ][:max_results]

    monkeypatch.setattr(search_api, "DuckDuckGoHTMLSearchClient", lambda: FakeClient())

    async with AsyncClient(
        transport=ASGITransport(app=main.app), base_url="http://test"
    ) as ac:
        r = await ac.get(
            "/api/auth/dev/login",
            params={"email": "a@example.com"},
            follow_redirects=False,
        )
        cookie = r.headers.get("set-cookie")
        ac.headers.update({"cookie": cookie.split(";", 1)[0]})

        r2 = await ac.post("/api/sessions", json={"prompt": "prompt"})
        sid = r2.json()["id"]

        r3 = await ac.post(
            f"/api/search/sessions/{sid}",
            params={"query": "ev market", "max_results": 2},
        )
        assert r3.status_code == 201
        body = r3.json()
        assert body["added"] == 2

        r4 = await ac.get(f"/api/sessions/{sid}")
        detail = r4.json()
        assert len(detail["sources"]) == 2
        assert any(s["url"] == "https://example.com" for s in detail["sources"])
