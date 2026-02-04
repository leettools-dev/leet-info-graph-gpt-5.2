from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture(autouse=True)
def _set_required_env(monkeypatch, tmp_path) -> None:
    """Ensure required Settings env vars exist for tests in this folder.

    Note: app/tests has its own conftest with a more complete setup; this is
    only for backend/tests which import settings at collection time.
    """

    monkeypatch.setenv("INFOGRAPH_SECRET_KEY", "test-" + "x" * 32)
    monkeypatch.setenv(
        "INFOGRAPH_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/test.db"
    )


@pytest.fixture
async def test_db_session(tmp_path) -> AsyncSession:
    """Create a fresh SQLite DB and yield an AsyncSession."""

    db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
    engine = create_async_engine(db_url, future=True)

    async with engine.begin() as conn:
        from app.db.base import Base

        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()
