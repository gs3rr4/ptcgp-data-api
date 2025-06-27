# pragma: no cover
# ruff: noqa: E402
# flake8: noqa
import os
from pathlib import Path

os.environ.setdefault("DATA_DIR", str(Path(__file__).parent / "../data"))
os.environ["SKIP_IMAGE_CHECKS"] = "1"
os.environ["API_KEY"] = "testkey"

import pytest
from fastapi.testclient import TestClient
from ptcgp_api import app  # noqa: E402

pytest.importorskip("pytest_benchmark")

client = TestClient(app)


def test_cards_filter_benchmark(benchmark):
    def run():
        client.get("/cards", params={"type": "Metal", "limit": 20})

    benchmark(run)
