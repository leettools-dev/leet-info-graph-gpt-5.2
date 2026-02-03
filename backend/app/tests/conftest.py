from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture()
def app_env(tmp_path, monkeypatch) -> None:
    """Default env for backend tests.

    Ensures Settings are configured consistently across tests without relying on
    import order.
    """

    monkeypatch.setenv(
        "INFOGRAPH_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/test.db"
    )
    monkeypatch.setenv("INFOGRAPH_GOOGLE_CLIENT_ID", "test-client")
    monkeypatch.setenv("INFOGRAPH_GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("INFOGRAPH_SECRET_KEY", "test-" + "x" * 32)


@pytest.fixture()
def test_app(app_env):
    # Import after env is set.
    from importlib import reload

    import app.core.config as config

    reload(config)

    import app.db.session as session

    reload(session)

    import app.main as main

    reload(main)
    return main.app


@pytest.fixture()
async def client(test_app) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac
