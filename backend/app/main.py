from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, ingest, jobs, search, sessions
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Research Infograph Assistant API", lifespan=lifespan)

# Minimal in-process queue/worker for async research + rendering jobs (MVP).
# In production, replace with a durable queue + separate worker.
from app.services.jobs import InProcessJobQueue

app.state.job_queue = InProcessJobQueue()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve locally stored media (dev/MVP). In production this should be served by a CDN/bucket.
# Ensure directory exists to avoid import-time errors.
import os

os.makedirs(settings.media_root, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.media_root), name="media")


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


app.include_router(auth.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
