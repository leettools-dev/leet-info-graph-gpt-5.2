from __future__ import annotations

import pytest

from app.services.web_search import (
    RateLimitError,
    SimpleTTLCache,
    TokenBucketRateLimiter,
    DuckDuckGoHTMLSearchClient,
)


def test_simple_ttl_cache_validates_inputs() -> None:
    with pytest.raises(ValueError):
        SimpleTTLCache(ttl_seconds=0)
    with pytest.raises(ValueError):
        SimpleTTLCache(max_items=0)


def test_token_bucket_rate_limiter_validates_inputs() -> None:
    with pytest.raises(ValueError):
        TokenBucketRateLimiter(rate_per_minute=0)


@pytest.mark.asyncio
async def test_ddg_client_rate_limited_when_no_tokens() -> None:
    limiter = TokenBucketRateLimiter(rate_per_minute=1)
    # Exhaust token
    assert limiter.allow() is True
    assert limiter.allow() is False

    # When no tokens are available, acquire_or_raise should fail fast.
    with pytest.raises(RateLimitError):
        await limiter.acquire_or_raise()
