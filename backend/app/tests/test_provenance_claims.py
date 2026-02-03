import pytest


@pytest.mark.asyncio
async def test_infographic_generation_includes_claims_with_source_ids(client):
    # dev login sets cookie via redirect
    r = await client.get(
        "/api/auth/dev/login",
        params={"email": "a@example.com"},
        follow_redirects=False,
    )
    assert r.status_code in (302, 307)
    cookie = r.headers.get("set-cookie")
    assert cookie and "session=" in cookie
    client.headers.update({"cookie": cookie.split(";", 1)[0]})

    # Create session
    res = await client.post("/api/sessions", json={"prompt": "EV market trends"})
    assert res.status_code == 201
    session_id = res.json()["id"]

    # Add two sources
    res = await client.post(
        f"/api/sessions/{session_id}/sources",
        params={
            "title": "Source A",
            "url": "https://example.com/a",
            "snippet": "A snippet",
            "confidence": 0.9,
        },
    )
    assert res.status_code == 201
    src_a_id = res.json()["id"]

    res = await client.post(
        f"/api/sessions/{session_id}/sources",
        params={
            "title": "Source B",
            "url": "https://example.com/b",
            "snippet": "B snippet",
            "confidence": 0.8,
        },
    )
    assert res.status_code == 201
    src_b_id = res.json()["id"]

    # Generate infographic
    res = await client.post(f"/api/sessions/{session_id}/infographic")
    assert res.status_code == 201
    data = res.json()

    assert "claims" in data
    assert isinstance(data["claims"], list)
    assert len(data["claims"]) >= 1

    claim = data["claims"][0]
    assert claim["id"]
    assert claim["text"]
    assert claim["source_ids"] == [src_a_id, src_b_id]

    # Also verify session detail exposes claims via infographic
    res = await client.get(f"/api/sessions/{session_id}")
    assert res.status_code == 200
    detail = res.json()
    assert detail["infographic"] is not None
    assert "claims" in detail["infographic"]
    assert detail["infographic"]["claims"][0]["source_ids"] == [src_a_id, src_b_id]
