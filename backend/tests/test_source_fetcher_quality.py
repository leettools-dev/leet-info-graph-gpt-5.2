import pytest

from app.services.source_fetcher import ContentQualityError, HTTPSourceFetcher


class _Resp:
    def __init__(self, text: str, headers: dict[str, str] | None = None, status_code: int = 200):
        self.text = text
        self.headers = headers or {}
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("http error")


class _Client:
    def __init__(self, resp: _Resp):
        self._resp = resp

    async def get(self, url: str, headers: dict[str, str] | None = None) -> _Resp:  # noqa: ARG002
        return self._resp


@pytest.mark.asyncio
async def test_fetch_rejects_non_html_content_type() -> None:
    fetcher = HTTPSourceFetcher(
        http_client=_Client(_Resp("{}", headers={"content-type": "application/json"})),
        min_text_length=1,
    )
    with pytest.raises(ContentQualityError):
        await fetcher.fetch("https://example.com/data.json")


@pytest.mark.asyncio
async def test_fetch_rejects_block_page() -> None:
    html = "<html><title>Attention Required</title><body>captcha verify you are human</body></html>"
    fetcher = HTTPSourceFetcher(
        http_client=_Client(_Resp(html, headers={"content-type": "text/html"})),
        min_text_length=1,
    )
    with pytest.raises(ContentQualityError):
        await fetcher.fetch("https://example.com")


@pytest.mark.asyncio
async def test_fetch_rejects_too_short_text() -> None:
    html = "<html><title>Hi</title><body><p>tiny</p></body></html>"
    fetcher = HTTPSourceFetcher(
        http_client=_Client(_Resp(html, headers={"content-type": "text/html"})),
        min_text_length=50,
    )
    with pytest.raises(ContentQualityError):
        await fetcher.fetch("https://example.com")


@pytest.mark.asyncio
async def test_fetch_truncates_long_text() -> None:
    long_text = "word " * 1000
    html = f"<html><title>Long</title><body><p>{long_text}</p></body></html>"
    fetcher = HTTPSourceFetcher(
        http_client=_Client(_Resp(html, headers={"content-type": "text/html"})),
        min_text_length=1,
        max_text_length=100,
    )
    fetched = await fetcher.fetch("https://example.com")
    assert len(fetched.text) == 100
