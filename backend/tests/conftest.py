from __future__ import annotations

import pytest


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
