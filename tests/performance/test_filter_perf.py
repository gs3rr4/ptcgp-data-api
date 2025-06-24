# ruff: noqa: E402
# flake8: noqa
import os

import pytest
from fastapi.testclient import TestClient
from main import app

os.environ["SKIP_IMAGE_CHECKS"] = "1"
os.environ["API_KEY"] = "testkey"

pytest.importorskip("pytest_benchmark")

client = TestClient(app)


def test_cards_filter_benchmark(benchmark):
    def run():
        client.get("/cards", params={"type": "Metal", "limit": 20})

    benchmark(run)
