import logging
import os
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")),
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402
import ptcgp_api.routes.users as users_routes  # noqa: E402

os.environ["SKIP_IMAGE_CHECKS"] = "1"
os.environ["API_KEY"] = "testkey"

HEADERS = {"X-API-Key": "testkey"}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def disable_network(monkeypatch, client):
    """Avoid real network calls during tests."""

    class DummyResp:
        status_code = 200

    async def dummy_head(url, *_, **__):
        return DummyResp()

    monkeypatch.setattr(client.app.state.http_client, "head", dummy_head)


def test_cards_returns_list(client):
    response = client.get("/cards")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_sets_returns_list(client):
    response = client.get("/sets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_events_returns_list(client):
    response = client.get("/events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_tournaments_returns_list(client):
    response = client.get("/tournaments")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_card_by_id(client):
    resp = client.get("/cards/001")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("id") == "001"


def test_search_cards(client):
    response = client.get(
        "/cards/search",
        params={"q": "Arceus", "fields": "name"},
    )
    assert response.status_code == 200
    data = response.json()
    assert any(card["id"] == "001" for card in data)


def test_missing_api_key_rejected(client):
    resp = client.post("/decks", json={"name": "Fail", "cards": ["001"]})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Ungültiger oder fehlender API-Schlüssel"


def test_invalid_api_key_rejected(client):
    resp = client.post(
        "/decks",
        json={"name": "Fail", "cards": ["001"]},
        headers={"X-API-Key": "wrong"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Ungültiger oder fehlender API-Schlüssel"


def test_user_endpoints(client):
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


def test_deck_and_group_flow(client, caplog):
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
    resp = client.post(
        f"/decks/{deck_id}/vote",
        params={"vote": "up"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["votes"] == 1
    assert any("Created deck" in r.message for r in caplog.records)

    # create group
    resp = client.post(
        "/groups",
        json={"name": "Test Group"},
        headers=HEADERS,
    )
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


def test_get_unknown_card(client):
    resp = client.get("/cards/unknown")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Karte nicht gefunden"


def test_get_unknown_set(client):
    resp = client.get("/sets/unknown")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Set nicht gefunden"


def test_trade_matches_empty(client, monkeypatch):
    monkeypatch.setattr(users_routes, "_users", {})
    resp = client.get("/trades/matches")
    assert resp.status_code == 200
    assert resp.json() == []


def test_validation_errors(client):
    resp = client.post(
        "/decks",
        json={"cards": "foo"},
        headers=HEADERS,
    )
    assert resp.status_code == 422

    resp = client.post(
        "/groups",
        json={},
        headers=HEADERS,
    )
    assert resp.status_code == 422

    resp = client.post(
        "/users/alice/have",
        json={"cards": "foo"},
        headers=HEADERS,
    )
    assert resp.status_code == 422


def test_invalid_vote_value(client):
    resp = client.post(
        "/decks/1/vote",
        params={"vote": "invalid"},
        headers=HEADERS,
    )
    assert resp.status_code == 422


def test_invalid_lang_rejected(client):
    resp = client.get("/cards", params={"lang": "xx"})
    assert resp.status_code == 422


def test_http_client_closed_after_shutdown():
    with TestClient(app) as local:
        assert not local.app.state.http_client.is_closed
    assert local.app.state.http_client.is_closed
