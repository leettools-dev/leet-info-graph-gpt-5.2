from __future__ import annotations

from dataclasses import dataclass

from app.services.source_fetcher import HTTPSourceFetcher
from app.services.summarizer import SimpleSummarizer, Summary


@dataclass(frozen=True)
class IngestedSource:
    url: str
    title: str | None
    snippet: str | None
    summary: Summary


class IngestPipeline:
    """Fetch + parse + summarize pipeline for a single source URL."""

    def __init__(
        self,
        *,
        fetcher: HTTPSourceFetcher | None = None,
        summarizer: SimpleSummarizer | None = None,
    ) -> None:
        self.fetcher = fetcher or HTTPSourceFetcher()
        self.summarizer = summarizer or SimpleSummarizer()

    async def ingest(self, url: str) -> IngestedSource:
        fetched = await self.fetcher.fetch(url)
        summary = self.summarizer.summarize(
            url=fetched.url, title=fetched.title, text=fetched.text
        )
        snippet = None
        if summary.summary:
            snippet = summary.summary[:240]
        return IngestedSource(
            url=fetched.url, title=fetched.title, snippet=snippet, summary=summary
        )
