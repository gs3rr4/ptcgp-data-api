import os
from pathlib import Path

os.environ.setdefault("DATA_DIR", str(Path(__file__).parent / "data"))

from ptcgp_api.data import build_search_index, filter_language  # noqa: E402


def test_build_search_index():
    cards = [
        {
            "id": "001",
            "name": {"de": "Test", "en": "Test"},
            "abilities": [{"name": {"de": "F"}, "effect": {"de": "E"}}],
            "attacks": [{"name": {"de": "A"}, "effect": {"de": "B"}}],
        }
    ]
    index = build_search_index(cards)
    assert "001" in index
    assert "de" in index["001"]
    assert "test" in index["001"]["de"]["name"]


def test_filter_language():
    data = {"de": "Hallo", "en": "Hi"}
    assert filter_language(data, "de") == "Hallo"
    assert filter_language(data, "en") == "Hi"
