from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

import httpx

from app.services.web_search import SimpleTTLCache, TokenBucketRateLimiter


class FetchError(RuntimeError):
    """Raised when fetching a source URL fails."""


class ContentQualityError(RuntimeError):
    """Raised when fetched content is missing/too low quality for summarization."""


@dataclass(frozen=True)
class FetchedSource:
    """Fetched and lightly-parsed representation of a web page."""

    url: str
    title: str | None
    text: str
    content_type: str | None = None
    status_code: int | None = None
    fetched_at_epoch: float | None = None


class HTTPSourceFetcher:
    """Fetch web pages with caching and rate limiting.

    This implements the "ingest" part of the pipeline: given a URL, fetch the
    HTML, extract a title and plain-ish text.

    Reliability notes (MVP):
    - Reject obviously non-HTML responses.
    - Detect likely block pages / CAPTCHAs.
    - Enforce minimum text length.
    """

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient | None = None,
        cache: SimpleTTLCache | None = None,
        rate_limiter: TokenBucketRateLimiter | None = None,
        cache_ttl_seconds: int = 60 * 60,
        cache_max_items: int = 512,
        rate_per_minute: int = 30,
        min_text_length: int = 400,
        max_text_length: int = 60_000,
    ) -> None:
        self._http = http_client or httpx.AsyncClient(timeout=20, follow_redirects=True)
        self._cache = cache or SimpleTTLCache(
            ttl_seconds=cache_ttl_seconds, max_items=cache_max_items
        )
        self._rate_limiter = rate_limiter or TokenBucketRateLimiter(
            rate_per_minute=rate_per_minute
        )
        self._min_text_length = min_text_length
        self._max_text_length = max_text_length

    def _cache_key(self, url: str) -> str:
        return hashlib.sha256(f"fetch:{url}".encode("utf-8")).hexdigest()

    async def fetch(self, url: str) -> FetchedSource:
        url = url.strip()
        if not url:
            raise FetchError("url is required")

        key = self._cache_key(url)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        if not self._rate_limiter.allow():
            raise FetchError("Fetch rate limit exceeded")

        started = time.time()
        try:
            resp = await self._http.get(url, headers={"user-agent": "Mozilla/5.0"})
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise FetchError(f"Failed to fetch url: {url}") from exc

        content_type = (resp.headers.get("content-type") or "").lower().strip()
        if content_type and "text/html" not in content_type and "application/xhtml" not in content_type:
            raise ContentQualityError(
                f"Unsupported content-type for url {url}: {content_type}"
            )

        html = resp.text
        if _looks_like_block_page(html):
            raise ContentQualityError(f"Blocked or bot-detection page for url: {url}")

        title = _extract_title(html)
        text = _html_to_text(html)
        text = _normalize_whitespace(text)
        if len(text) > self._max_text_length:
            text = text[: self._max_text_length]
        if len(text) < self._min_text_length:
            raise ContentQualityError(
                f"Insufficient text extracted from url: {url} (len={len(text)})"
            )

        fetched = FetchedSource(
            url=url,
            title=title,
            text=text,
            content_type=content_type or None,
            status_code=resp.status_code,
            fetched_at_epoch=started,
        )
        self._cache.set(key, fetched)

        return fetched


def _extract_title(html: str) -> str | None:
    lower = html.lower()
    start = lower.find("<title")
    if start == -1:
        return None
    gt = lower.find(">", start)
    if gt == -1:
        return None
    end = lower.find("</title>", gt)
    if end == -1:
        return None
    title = html[gt + 1 : end]
    return " ".join(_html_to_text(title).split()) or None


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace while preserving paragraph breaks."""

    lines = [" ".join(line.split()) for line in text.splitlines()]
    # Keep non-empty lines; cap consecutive blanks to a single blank line
    out: list[str] = []
    blank = False
    for line in lines:
        if not line.strip():
            if not blank:
                out.append("")
            blank = True
            continue
        blank = False
        out.append(line)
    normalized = "\n".join(out).strip()
    return normalized


def _looks_like_block_page(html: str) -> bool:
    """Heuristically detect bot-detection / block pages."""

    lower = html.lower()
    indicators = [
        "captcha",
        "cloudflare",
        "attention required",
        "verify you are human",
        "unusual traffic",
        "access denied",
        "temporary blocked",
    ]
    return any(ind in lower for ind in indicators)


def _html_to_text(html: str) -> str:
    """Very small HTML-to-text conversion without external dependencies."""

    lower = html.lower()
    out: list[str] = []
    i = 0
    while i < len(html):
        if lower.startswith("<script", i):
            end = lower.find("</script>", i)
            if end == -1:
                break
            i = end + len("</script>")
            continue
        if lower.startswith("<style", i):
            end = lower.find("</style>", i)
            if end == -1:
                break
            i = end + len("</style>")
            continue

        ch = html[i]
        if ch == "<":
            end = html.find(">", i)
            if end == -1:
                break
            tag = lower[i + 1 : end].strip()
            if tag.startswith("br") or tag.startswith("p") or tag.startswith("/p"):
                out.append("\n")
            i = end + 1
            continue

        out.append(ch)
        i += 1

    cleaned = "".join(out)
    return (
        cleaned.replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
