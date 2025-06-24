import os
import logging
from cachetools import TTLCache
import httpx
import pytest

import ptcgp_api.routes.cards as cards_routes

pytestmark = pytest.mark.asyncio


async def test_image_url_cache(monkeypatch):
    calls = []
    os.environ.pop("SKIP_IMAGE_CHECKS", None)

    class DummyClient:
        async def head(self, url, timeout=3):
            calls.append(url)

            class R:
                status_code = 200

            return R()

    client = DummyClient()
    monkeypatch.setattr(
        cards_routes,
        "_image_cache",
        TTLCache(maxsize=10, ttl=10),
    )

    url1 = await cards_routes._image_url(client, "de", "A2a", "001")
    url2 = await cards_routes._image_url(client, "de", "A2a", "001")
    assert url1 == url2
    assert len(calls) == 1


async def test_image_url_timeout(monkeypatch, caplog):
    os.environ.pop("SKIP_IMAGE_CHECKS", None)

    class DummyClient:
        async def head(self, url, timeout=3):
            raise httpx.TimeoutException("boom")

    client = DummyClient()

    cache = TTLCache(maxsize=10, ttl=10)
    monkeypatch.setattr(cards_routes, "_image_cache", cache)

    caplog.set_level(logging.ERROR)
    url = await cards_routes._image_url(
        client,
        "de",
        "A2a",
        "001",
    )
    assert url.endswith("low.webp")
    high = "https://assets.tcgdex.net/de/tcgp/A2a/001/high.webp"
    assert cache[high] is False
    assert any("HEAD request failed" in r.message for r in caplog.records)


async def test_image_url_retry(monkeypatch):
    os.environ.pop("SKIP_IMAGE_CHECKS", None)

    calls = []

    class DummyClient:
        def __init__(self):
            self.first = True

        async def head(self, url, timeout=3):
            calls.append(url)
            if self.first:
                self.first = False
                raise httpx.HTTPError("boom")

            class R:
                status_code = 200

            return R()

    client = DummyClient()
    monkeypatch.setattr(
        cards_routes,
        "_image_cache",
        TTLCache(maxsize=10, ttl=10),
    )
    url = await cards_routes._image_url(client, "de", "A2a", "001")
    assert url.endswith("high.webp")
    assert len(calls) == 2
