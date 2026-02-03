from __future__ import annotations

import asyncio
from datetime import datetime

import pytest

from app.services.jobs import InProcessJobQueue, Job


@pytest.mark.asyncio
async def test_in_process_job_queue_transitions_to_succeeded():
    q = InProcessJobQueue()
    job = Job(job_id="j1", kind="test", created_at=datetime.utcnow())

    async def work() -> dict:
        await asyncio.sleep(0)
        return {"ok": True}

    await q.enqueue(job=job, coro_factory=work)

    # allow the task to run
    await asyncio.sleep(0)

    status = await q.get_status("j1")
    assert status is not None
    assert status.state in {"queued", "running", "succeeded"}

    # wait a tiny bit more to finish
    for _ in range(10):
        st = await q.get_status("j1")
        if st and st.state == "succeeded":
            assert st.result == {"ok": True}
            return
        await asyncio.sleep(0)

    st = await q.get_status("j1")
    assert st is not None
    assert st.state == "succeeded"
