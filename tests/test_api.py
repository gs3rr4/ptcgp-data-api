import os
import sys
import pytest
import requests

# Skip external image checks during tests
os.environ["SKIP_IMAGE_CHECKS"] = "1"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def disable_network(monkeypatch):
    """Avoid real network calls during tests."""

    def fake_image_url(lang: str, set_id: str, local_id: str) -> str:
        return f"/mock/{lang}/{set_id}/{local_id}.webp"

    class DummyResp:
        status_code = 200

    monkeypatch.setattr("main._image_url", fake_image_url)
    monkeypatch.setattr(requests, "head", lambda *a, **k: DummyResp())


def test_cards_returns_list():
    response = client.get("/cards")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_sets_returns_list():
    response = client.get("/sets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_events_returns_list():
    response = client.get("/events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_tournaments_returns_list():
    response = client.get("/tournaments")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_card_by_id():
    resp = client.get("/cards/001")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("id") == "001"


def test_search_cards():
    response = client.get("/cards/search", params={"q": "Arceus", "fields": "name"})
    assert response.status_code == 200
    data = response.json()
    assert any(card["id"] == "001" for card in data)


def test_user_endpoints():
    user = "alice"
    have_cards = ["001"]
    want_cards = ["002"]

    resp = client.post(f"/users/{user}/have", json={"cards": have_cards})
    assert resp.status_code == 200

    resp = client.post(f"/users/{user}/want", json={"cards": want_cards})
    assert resp.status_code == 200

    resp = client.get(f"/users/{user}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["have"] == have_cards
    assert data["want"] == want_cards


def test_deck_and_group_flow():
    # create deck
    resp = client.post("/decks", json={"name": "Test Deck", "cards": ["001"]})
    assert resp.status_code == 200
    deck = resp.json()
    deck_id = deck["id"]

    # list decks
    resp = client.get("/decks")
    assert resp.status_code == 200
    assert any(d["id"] == deck_id for d in resp.json())

    # get deck
    resp = client.get(f"/decks/{deck_id}")
    assert resp.status_code == 200

    # vote deck
    resp = client.post(f"/decks/{deck_id}/vote", params={"vote": "up"})
    assert resp.status_code == 200
    assert resp.json()["votes"] == 1

    # create group
    resp = client.post("/groups", json={"name": "Test Group"})
    assert resp.status_code == 200
    group = resp.json()
    group_id = group["id"]

    user = "bob"
    resp = client.post(f"/groups/{group_id}/join", json={"user_id": user})
    assert resp.status_code == 200
    assert user in resp.json()["members"]

    resp = client.get(f"/groups/{group_id}")
    assert resp.status_code == 200
    assert user in resp.json()["members"]


def test_get_unknown_card():
    resp = client.get("/cards/unknown")
    assert resp.status_code == 404


def test_get_unknown_set():
    resp = client.get("/sets/unknown")
    assert resp.status_code == 404


def test_trade_matches_empty(monkeypatch):
    import main

    monkeypatch.setattr(main, "_users", {})
    resp = client.get("/trades/matches")
    assert resp.status_code == 200
    assert resp.json() == []


def test_validation_errors():
    resp = client.post("/decks", json={"cards": "foo"})
    assert resp.status_code == 422

    resp = client.post("/groups", json={})
    assert resp.status_code == 422

    resp = client.post("/users/alice/have", json={"cards": "foo"})
    assert resp.status_code == 422
