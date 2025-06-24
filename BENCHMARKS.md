# Benchmarks

Die folgenden Werte wurden mit `pytest --benchmark-only` auf einem kleinen
Testsystem ermittelt (FastAPI TestClient, Python 3.12):

| Test | Zeit |
| --- | --- |
| `test_cards_filter_benchmark` | ~2.5 ms |

Die exakten Zahlen können je nach Hardware variieren. Die Benchmarks helfen,
Regressionen schnell zu erkennen.
