from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Summary:
    url: str
    title: str | None
    summary: str
    key_points: list[str]


class SimpleSummarizer:
    """Very small deterministic summarizer.

    MVP: extracts the first few non-empty lines/sentences from the fetched text.
    In later phases this can be swapped for an LLM-based summarizer.
    """

    def __init__(self, *, max_chars: int = 800, max_points: int = 5) -> None:
        self.max_chars = max_chars
        self.max_points = max_points

    def summarize(self, *, url: str, title: str | None, text: str) -> Summary:
        cleaned = " ".join(text.split())
        cleaned = cleaned.strip()
        if not cleaned:
            return Summary(url=url, title=title, summary="", key_points=[])

        summary = cleaned[: self.max_chars]
        # naive bullet extraction
        parts = [p.strip() for p in summary.split(".") if p.strip()]
        key_points = [f"- {p}." for p in parts[: self.max_points]]
        return Summary(url=url, title=title, summary=summary, key_points=key_points)
