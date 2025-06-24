import os
import sys
import pytest
from fastapi.testclient import TestClient

os.environ["SKIP_IMAGE_CHECKS"] = "1"
os.environ["API_KEY"] = "testkey"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from main import app

pytest.importorskip("pytest_benchmark")

client = TestClient(app)


def test_cards_filter_benchmark(benchmark):
    def run():
        client.get("/cards", params={"type": "Metal", "limit": 20})

    benchmark(run)
