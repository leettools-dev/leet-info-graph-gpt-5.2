from __future__ import annotations

import pytest

from app.services.ingest import IngestPipeline


@pytest.mark.asyncio
async def test_ingest_pipeline_truncates_text_for_summarization() -> None:
    # Use a fetcher that returns a large text payload.
    from app.services.source_fetcher import FetchedSource

    class _Fetcher:
        async def fetch(self, url: str) -> FetchedSource:  # type: ignore[override]
            return FetchedSource(
                url=url,
                title="Example",
                text="x" * 10_000,
                content_type="text/html",
                status_code=200,
                fetched_at_epoch=0.0,
            )

    pipeline = IngestPipeline(fetcher=_Fetcher(), max_chars=1234)
    ingested = await pipeline.ingest("https://example.com")

    assert ingested.url == "https://example.com"
    assert ingested.summary is not None
    # Ensure snippet length is bounded by the summarizer max_chars.
    assert len(ingested.summary.summary) <= 800
