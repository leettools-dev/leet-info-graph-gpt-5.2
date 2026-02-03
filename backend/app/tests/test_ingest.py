import pytest


@pytest.mark.asyncio
async def test_ingest_endpoint_requires_auth(client):
    r = await client.post("/api/ingest/sessions/1")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_ingest_fills_snippet_and_updates_status(monkeypatch, client):
    from app.api import ingest as ingest_api

    class FakeFetcher:
        async def fetch(self, url: str):
            return type(
                "Fetched",
                (),
                {
                    "url": url,
                    "title": "Fetched Title",
                    "text": "This is a fetched page. It has content. More content.",
                },
            )()

    # Patch the pipeline constructor inside the module by swapping HTTPSourceFetcher
    monkeypatch.setattr(ingest_api, "HTTPSourceFetcher", lambda **_: FakeFetcher())

    # Login
    r = await client.get(
        "/api/auth/dev/login",
        params={"email": "a@example.com"},
        follow_redirects=False,
    )
    cookie = r.headers.get("set-cookie")
    client.headers.update({"cookie": cookie.split(";", 1)[0]})

    # Create session and add a source without snippet
    r2 = await client.post("/api/sessions", json={"prompt": "prompt"})
    sid = r2.json()["id"]
    r3 = await client.post(
        f"/api/sessions/{sid}/sources",
        params={"title": "T", "url": "https://example.com/x", "snippet": ""},
    )
    assert r3.status_code == 201

    # Ingest
    r4 = await client.post(f"/api/ingest/sessions/{sid}", params={"max_sources": 5})
    assert r4.status_code == 201
    assert r4.json()["processed"] == 1

    # Session now has snippet and status=ingested
    r5 = await client.get(f"/api/sessions/{sid}")
    body = r5.json()
    assert body["status"] == "ingested"
    assert body["sources"][0]["snippet"]
