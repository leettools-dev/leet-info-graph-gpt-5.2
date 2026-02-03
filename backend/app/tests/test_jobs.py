from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_async_run_endpoint_returns_job_id(client):
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

    # create session
    res = await client.post(
        "/api/sessions",
        json={"prompt": "Summarize EV market trends"},
    )
    assert res.status_code == 201
    session_id = res.json()["id"]

    # kick off async run
    res2 = await client.post(
        f"/api/sessions/{session_id}/run",
    )
    assert res2.status_code == 202
    job_id = res2.json()["job_id"]
    assert isinstance(job_id, str)
    assert job_id

    # poll job status (may still be running)
    res3 = await client.get(f"/api/jobs/{job_id}")
    assert res3.status_code == 200
    body = res3.json()
    assert body["job_id"] == job_id
    assert body["state"] in {"queued", "running", "succeeded", "failed"}
