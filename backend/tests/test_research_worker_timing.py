from __future__ import annotations

import pytest

from app.services.research_worker import run_research_and_render


class _FakeSearchClient:
    def __init__(self, hits):
        self._hits = hits

    async def search(self, _query: str):
        return self._hits


class _FakeIngestPipeline:
    def __init__(self, *, max_chars: int):
        self.max_chars = max_chars

    async def ingest(self, url: str):
        return type(
            "Ingested",
            (),
            {"title": "T", "url": url, "snippet": "S"},
        )()



@pytest.mark.asyncio
async def test_research_worker_returns_timing_ms(test_db_session):
    # Create a minimal session row via the DB model used by the worker.
    from app.models import ResearchSession

    s = ResearchSession(user_id=1, prompt="test prompt", status="queued")
    test_db_session.add(s)
    await test_db_session.commit()
    await test_db_session.refresh(s)

    # Avoid network calls by swapping dependencies inside the module.
    from app.services import research_worker as rw

    hits = [type("Hit", (), {"title": "H", "url": "https://example.com", "snippet": "snip"})()]
    rw.DuckDuckGoHTMLSearchClient = lambda: _FakeSearchClient(hits)  # type: ignore[assignment]
    rw.IngestPipeline = _FakeIngestPipeline  # type: ignore[assignment]

    result = await run_research_and_render(session_id=s.id, db=test_db_session)

    assert result["session_id"] == s.id
    assert "timing_ms" in result

    timing = result["timing_ms"]
    assert set(timing.keys()) == {"total", "search", "ingest", "render", "store"}
    for k, v in timing.items():
        assert isinstance(v, int)
        assert v >= 0
