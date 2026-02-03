from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_adoption_metrics_unauthenticated(client):
    res = await client.get("/api/metrics/adoption")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_adoption_metrics_user_sessions_count(client):
    # Login
    res = await client.get("/api/auth/dev/login?email=demo@example.com", follow_redirects=False)
    assert res.status_code in (302, 307)

    # Capture cookies from response and apply to client
    # httpx AsyncClient in tests keeps cookies automatically.

    # No sessions yet
    res0 = await client.get("/api/metrics/adoption")
    assert res0.status_code == 200
    data0 = res0.json()
    assert data0["sessions_in_window"] == 0
    assert data0["eligible_users"] == 0
    assert data0["users_with_2plus_sessions"] == 0
    assert data0["adoption_rate"] == 0.0

    # Create one session
    res1 = await client.post("/api/sessions", json={"prompt": "Test prompt 1"})
    assert res1.status_code == 201

    resm1 = await client.get("/api/metrics/adoption")
    assert resm1.status_code == 200
    data1 = resm1.json()
    assert data1["sessions_in_window"] == 1
    assert data1["eligible_users"] == 1
    assert data1["users_with_2plus_sessions"] == 0
    assert data1["adoption_rate"] == 0.0

    # Create second session
    res2 = await client.post("/api/sessions", json={"prompt": "Test prompt 2"})
    assert res2.status_code == 201

    resm2 = await client.get("/api/metrics/adoption")
    assert resm2.status_code == 200
    data2 = resm2.json()
    assert data2["sessions_in_window"] == 2
    assert data2["eligible_users"] == 1
    assert data2["users_with_2plus_sessions"] == 1
    assert data2["adoption_rate"] == 1.0


@pytest.mark.asyncio
async def test_adoption_metrics_days_clamped(client):
    res = await client.get("/api/auth/dev/login?email=demo2@example.com", follow_redirects=False)
    assert res.status_code in (302, 307)

    res2 = await client.get("/api/metrics/adoption?days=0")
    assert res2.status_code == 200
    assert res2.json()["window_days"] == 1

    res3 = await client.get("/api/metrics/adoption?days=9999")
    assert res3.status_code == 200
    assert res3.json()["window_days"] == 365
