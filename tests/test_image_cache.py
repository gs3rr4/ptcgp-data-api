import asyncio
import logging
import os
from cachetools import TTLCache
import httpx


import app.routes.cards as cards_routes


def test_image_url_cache(monkeypatch):
    calls = []

    os.environ.pop("SKIP_IMAGE_CHECKS", None)

    async def dummy_head(self, url, timeout=3):
        calls.append(url)

        class R:
            status_code = 200

        return R()

    monkeypatch.setattr(cards_routes, "_image_cache", TTLCache(maxsize=10, ttl=10))
    monkeypatch.setattr(httpx.AsyncClient, "head", dummy_head)

    url1 = asyncio.run(cards_routes._image_url("de", "A2a", "001"))
    url2 = asyncio.run(cards_routes._image_url("de", "A2a", "001"))
    assert url1 == url2
    assert len(calls) == 1


def test_image_url_timeout(monkeypatch, caplog):
    os.environ.pop("SKIP_IMAGE_CHECKS", None)

    async def timeout_head(self, url, timeout=3):
        raise httpx.TimeoutException("boom")

    cache = TTLCache(maxsize=10, ttl=10)
    monkeypatch.setattr(cards_routes, "_image_cache", cache)
    monkeypatch.setattr(httpx.AsyncClient, "head", timeout_head)

    caplog.set_level(logging.ERROR)
    url = asyncio.run(cards_routes._image_url("de", "A2a", "001"))
    assert url.endswith("low.webp")
    high = "https://assets.tcgdex.net/de/tcgp/A2a/001/high.webp"
    assert cache[high] is False
    assert any("HEAD request failed" in r.message for r in caplog.records)
