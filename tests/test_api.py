import os
import sys
import pytest
import logging

# Skip external image checks during tests
os.environ["SKIP_IMAGE_CHECKS"] = "1"
# Enable API key authentication for tests
os.environ["API_KEY"] = "testkey"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
import app as app_module
import app.routes.cards as cards_routes
import app.routes.users as users_routes

client = TestClient(app)

HEADERS = {"X-API-Key": "testkey"}


@pytest.fixture(autouse=True)
def disable_network(monkeypatch):
    """Avoid real network calls during tests."""

    async def fake_image_url(client, lang: str, set_id: str, local_id: str) -> str:
        return f"/mock/{lang}/{set_id}/{local_id}.webp"

    class DummyResp:
        status_code = 200

    monkeypatch.setattr(cards_routes, "_image_url", fake_image_url)

    class DummyClient:
        async def head(self, *_, **__):
            return DummyResp()

    app.dependency_overrides[app_module.get_client] = lambda: DummyClient()

    yield

    app.dependency_overrides.clear()


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


def test_missing_api_key_rejected():
    resp = client.post("/decks", json={"name": "Fail", "cards": ["001"]})
    assert resp.status_code == 401


def test_invalid_api_key_rejected():
    resp = client.post(
        "/decks",
        json={"name": "Fail", "cards": ["001"]},
        headers={"X-API-Key": "wrong"},
    )
    assert resp.status_code == 401


def test_user_endpoints():
    user = "alice"
    have_cards = ["001"]
    want_cards = ["002"]

    resp = client.post(
        f"/users/{user}/have", json={"cards": have_cards}, headers=HEADERS
    )
    assert resp.status_code == 200

    resp = client.post(
        f"/users/{user}/want", json={"cards": want_cards}, headers=HEADERS
    )
    assert resp.status_code == 200

    resp = client.get(f"/users/{user}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["have"] == have_cards
    assert data["want"] == want_cards


def test_deck_and_group_flow(caplog):
    caplog.set_level(logging.INFO)
    # create deck
    resp = client.post(
        "/decks", json={"name": "Test Deck", "cards": ["001"]}, headers=HEADERS
    )
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
    resp = client.post(f"/decks/{deck_id}/vote", params={"vote": "up"}, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["votes"] == 1
    assert any("Created deck" in r.message for r in caplog.records)

    # create group
    resp = client.post("/groups", json={"name": "Test Group"}, headers=HEADERS)
    assert resp.status_code == 200
    group = resp.json()
    group_id = group["id"]

    user = "bob"
    resp = client.post(
        f"/groups/{group_id}/join", json={"user_id": user}, headers=HEADERS
    )
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
    monkeypatch.setattr(users_routes, "_users", {})
    resp = client.get("/trades/matches")
    assert resp.status_code == 200
    assert resp.json() == []


def test_validation_errors():
    resp = client.post("/decks", json={"cards": "foo"}, headers=HEADERS)
    assert resp.status_code == 422

    resp = client.post("/groups", json={}, headers=HEADERS)
    assert resp.status_code == 422

    resp = client.post("/users/alice/have", json={"cards": "foo"}, headers=HEADERS)
    assert resp.status_code == 422


def test_invalid_vote_value():
    resp = client.post(
        "/decks/1/vote",
        params={"vote": "invalid"},
        headers=HEADERS,
    )
    assert resp.status_code == 422


def test_invalid_lang_rejected():
    resp = client.get("/cards", params={"lang": "xx"})
    assert resp.status_code == 422


def test_client_closed_on_shutdown():
    with TestClient(app) as local:
        local.get("/cards")
    from app import get_client

    assert get_client().is_closed


def test_card_not_found_message():
    resp = client.get("/cards/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Karte nicht gefunden"


def test_api_key_message(monkeypatch):
    resp = client.post("/decks", json={"name": "Fail", "cards": ["001"]})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Ungültiger oder fehlender API-Schlüssel"
