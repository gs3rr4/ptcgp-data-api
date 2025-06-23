import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

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
