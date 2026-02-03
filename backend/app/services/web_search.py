from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any

import httpx


class RateLimitError(RuntimeError):
    """Raised when an upstream call is blocked by rate limiting."""


@dataclass(frozen=True)
class SearchResult:
    """A single web search result."""

    title: str
    url: str
    snippet: str | None = None


class SimpleTTLCache:
    """In-memory TTL cache.

    This is intentionally small and process-local; it satisfies the MVP caching
    requirement and can later be replaced with Redis or a DB-backed cache.

    Note: This cache is *not* a strict LRU. When full, it evicts an arbitrary key.
    """

    def __init__(self, ttl_seconds: int = 3600, max_items: int = 512) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be > 0")
        if max_items <= 0:
            raise ValueError("max_items must be > 0")

        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._items: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._items.get(key)
        if not item:
            return None
        expires_at, value = item
        if time.time() >= expires_at:
            self._items.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        if len(self._items) >= self.max_items:
            # Drop an arbitrary item (simple policy for MVP)
            oldest_key = next(iter(self._items.keys()))
            self._items.pop(oldest_key, None)
        self._items[key] = (time.time() + self.ttl_seconds, value)


class TokenBucketRateLimiter:
    """Simple in-process token bucket rate limiter.

    This is a best-effort limiter meant to reduce upstream traffic.

    It exposes two APIs:
    - allow(): bool (non-blocking)
    - await acquire(): (blocking until a token is available)

    Note: This limiter is process-local (MVP). For multi-worker deployments,
    replace with a shared limiter (e.g., Redis).
    """

    def __init__(self, rate_per_minute: int = 30) -> None:
        if rate_per_minute <= 0:
            raise ValueError("rate_per_minute must be > 0")

        self.capacity = rate_per_minute
        self.tokens = float(self.capacity)
        self.refill_rate_per_sec = self.capacity / 60.0
        self.last = time.time()

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.last
        self.last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate_per_sec)

    def allow(self) -> bool:
        self._refill()
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

    async def acquire(self) -> None:
        """Wait until a token is available."""

        # Small sleep-based loop is sufficient for our MVP.
        while True:
            if self.allow():
                return
            await _sleep_for_token(self.refill_rate_per_sec)


async def _sleep_for_token(refill_rate_per_sec: float) -> None:
    # Avoid division by zero; refill_rate_per_sec is derived from rate_per_minute (>0)
    delay = max(0.05, min(1.0, 1.0 / refill_rate_per_sec))
    import asyncio

    await asyncio.sleep(delay)



class DuckDuckGoHTMLSearchClient:
    """Search via DuckDuckGo's public HTML endpoint.

    Note: This is best-effort and may be blocked or change without notice.
    For production, swap to a paid search API.
    """

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient | None = None,
        cache: SimpleTTLCache | None = None,
        rate_limiter: TokenBucketRateLimiter | None = None,
        cache_ttl_seconds: int = 60 * 60,
        cache_max_items: int = 512,
        rate_per_minute: int = 20,
    ) -> None:
        self._http = http_client or httpx.AsyncClient(timeout=20)
        self._cache = cache or SimpleTTLCache(
            ttl_seconds=cache_ttl_seconds, max_items=cache_max_items
        )
        self._rate_limiter = rate_limiter or TokenBucketRateLimiter(
            rate_per_minute=rate_per_minute
        )

    def _cache_key(self, query: str, max_results: int) -> str:
        raw = f"ddg:{query}:{max_results}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    async def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        if not query.strip():
            return []

        key = self._cache_key(query, max_results)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        # Prefer waiting over failing fast for better UX.
        await self._rate_limiter.acquire()

        # Use HTML endpoint and parse very lightly.
        resp = await self._http.post(
            "https://duckduckgo.com/html/",
            data={"q": query},
            headers={"user-agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()

        html = resp.text
        results: list[SearchResult] = []

        # Minimal parsing without bs4 dependency.
        # Look for result links with class="result__a".
        marker = 'class="result__a"'
        pos = 0
        while len(results) < max_results:
            idx = html.find(marker, pos)
            if idx == -1:
                break
            href_idx = html.rfind("href=", 0, idx)
            if href_idx == -1:
                pos = idx + len(marker)
                continue
            quote1 = html.find('"', href_idx)
            quote2 = html.find('"', quote1 + 1)
            url = html[quote1 + 1 : quote2]

            # Title text
            gt = html.find(">", idx)
            lt = html.find("</a>", gt)
            title = html[gt + 1 : lt]
            title = _strip_tags(title).strip()

            results.append(SearchResult(title=title or url, url=url, snippet=None))
            pos = lt

        self._cache.set(key, results)
        return results


def _strip_tags(text: str) -> str:
    """Very small helper to remove a few common HTML entities/tags."""

    out = []
    in_tag = False
    for ch in text:
        if ch == "<":
            in_tag = True
            continue
        if ch == ">":
            in_tag = False
            continue
        if not in_tag:
            out.append(ch)
    cleaned = "".join(out)
    return (
        cleaned.replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
