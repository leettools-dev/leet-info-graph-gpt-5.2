import pytest


@pytest.mark.asyncio
async def test_create_and_list_sessions_unauthenticated(client):
    r = await client.get("/api/sessions")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_create_and_get_session_authenticated(client):
    # dev login sets cookie via redirect
    r = await client.get(
        "/api/auth/dev/login",
        params={"email": "a@example.com"},
        follow_redirects=False,
    )
    assert r.status_code in (302, 307)
    cookie = r.headers.get("set-cookie")
    assert cookie and "session=" in cookie

    # carry cookie
    client.headers.update({"cookie": cookie.split(";", 1)[0]})

    r2 = await client.post("/api/sessions", json={"prompt": "test prompt"})
    assert r2.status_code == 201
    sid = r2.json()["id"]

    r3 = await client.get("/api/sessions")
    assert r3.status_code == 200
    assert len(r3.json()) == 1

    r4 = await client.get(f"/api/sessions/{sid}")
    assert r4.status_code == 200
    detail = r4.json()
    assert detail["prompt"] == "test prompt"
    assert detail["messages"][0]["role"] == "user"

    # Generate infographic
    r5 = await client.post(f"/api/sessions/{sid}/infographic")
    assert r5.status_code == 201
    info = r5.json()
    assert info["image_url"].startswith("data:image/svg+xml")
    assert info["layout_meta"]["title"]

    # Detail now includes infographic
    r6 = await client.get(f"/api/sessions/{sid}")
    assert r6.status_code == 200
    detail2 = r6.json()
    assert detail2["infographic"] is not None
    assert detail2["infographic"]["image_url"].startswith("data:image/svg+xml")

    # Export JSON
    r7 = await client.get(f"/api/sessions/{sid}/export.json")
    assert r7.status_code == 200
    exported = r7.json()
    assert exported["session"]["id"] == sid
    assert exported["session"]["prompt"] == "test prompt"
    assert isinstance(exported["messages"], list)

    # Export SVG
    r8 = await client.get(f"/api/sessions/{sid}/infographic.svg")
    assert r8.status_code == 200
    assert r8.headers["content-type"].startswith("image/svg+xml")
    assert "content-disposition" in {k.lower(): v for k, v in r8.headers.items()}
    assert r8.text.startswith("<svg")
