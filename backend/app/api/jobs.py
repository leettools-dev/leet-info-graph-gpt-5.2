from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.services.jobs import JobStatus

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
async def get_job_status(
    job_id: str,
    _user=Depends(get_current_user),
) -> dict:
    """Get async job status.

    Note: We authenticate the user, but the MVP queue is in-process and does not
    persist job ownership. A production job system must enforce ownership.
    """
    from app.main import app

    queue = getattr(app.state, "job_queue", None)
    if queue is None:
        raise HTTPException(status_code=500, detail="Job queue not configured")

    status: JobStatus | None = await queue.get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": status.job_id,
        "kind": status.kind,
        "state": status.state,
        "created_at": status.created_at.isoformat(),
        "started_at": status.started_at.isoformat() if status.started_at else None,
        "finished_at": status.finished_at.isoformat() if status.finished_at else None,
        "result": status.result,
        "error": status.error,
    }
