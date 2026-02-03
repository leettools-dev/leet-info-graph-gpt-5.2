from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable, Coroutine


@dataclass(frozen=True)
class Job:
    """A minimal in-process async job handle.

    This is intentionally lightweight and suitable for an MVP. In production,
    replace with a durable queue (e.g., Redis/RQ, Celery, ARQ).
    """

    job_id: str
    kind: str
    created_at: datetime


@dataclass(frozen=True)
class JobStatus:
    job_id: str
    kind: str
    state: str  # queued|running|succeeded|failed
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: dict | None = None
    error: str | None = None


class InProcessJobQueue:
    def __init__(self) -> None:
        self._jobs: dict[str, JobStatus] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def enqueue(
        self,
        *,
        job: Job,
        coro_factory: Callable[[], Coroutine[None, None, dict]],
    ) -> None:
        async with self._lock:
            self._jobs[job.job_id] = JobStatus(
                job_id=job.job_id,
                kind=job.kind,
                state="queued",
                created_at=job.created_at,
            )

            async def _runner() -> None:
                async with self._lock:
                    current = self._jobs[job.job_id]
                    self._jobs[job.job_id] = JobStatus(
                        **{
                            **current.__dict__,
                            "state": "running",
                            "started_at": datetime.utcnow(),
                        }
                    )
                try:
                    result = await coro_factory()
                    async with self._lock:
                        current2 = self._jobs[job.job_id]
                        self._jobs[job.job_id] = JobStatus(
                            **{
                                **current2.__dict__,
                                "state": "succeeded",
                                "finished_at": datetime.utcnow(),
                                "result": result,
                            }
                        )
                except Exception as e:  # pragma: no cover
                    async with self._lock:
                        current2 = self._jobs[job.job_id]
                        self._jobs[job.job_id] = JobStatus(
                            **{
                                **current2.__dict__,
                                "state": "failed",
                                "finished_at": datetime.utcnow(),
                                "error": str(e),
                            }
                        )

            self._tasks[job.job_id] = asyncio.create_task(_runner())

    async def get_status(self, job_id: str) -> JobStatus | None:
        async with self._lock:
            return self._jobs.get(job_id)
