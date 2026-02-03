from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, sessions
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

app = FastAPI(title="Research Infograph Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"] ,
)


@app.on_event("startup")
async def startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


app.include_router(auth.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
