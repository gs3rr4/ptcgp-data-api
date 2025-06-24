# Changelog

## [Unreleased]
### Added
- Asynchronous image checks using `httpx.AsyncClient` with TTL cache.
- Error logging for failed image requests.
- Application refactored into `app` package with modular routers.
- Data loading moved to `app/data.py`.
- Configurable logging with `LOG_LEVEL` and startup/deck creation logs.
- CORS origins configurable via `ALLOW_ORIGINS` environment variable.
- Optional API key authentication for write operations using the `API_KEY`
  environment variable and `X-API-Key` header.
- Filter indexes for sets, types and rarity for faster `/cards` queries.
- Optional profiling via `PROFILE_FILTERS` environment variable.
- Benchmark test suite in `tests/performance` (requires `pytest-benchmark`).
- `Language` and `VoteDirection` enums for better validation.
- `DATA_DIR` environment variable to configure the data path.
- Global exception handler that logs unexpected errors.
- GitHub Actions workflow with `ruff` linting and tests.
- `IMAGE_TIMEOUT` environment variable for configurable image request timeout.
- Package versions pinned in `requirements*.txt` for reproducible installs.
- Coverage reporting via `pytest-cov` in CI.

### Changed
- Endpoints now await image URL resolution.
- Image URL checks cached for 24 hours to improve performance.
- CI workflow uses `ruff check` for compatibility.
- Async tests share a session-scoped event loop.


## [1.1.0] - 2025-06-26
### Added
- Structured JSON logging via structlog with rotating file handler.
- Lifespan management closing the HTTP client on shutdown.
- Pre-commit configuration with Black, Ruff and Flake8.
- Security scanning with pip-audit in CI.
- Example environment file `.env.example`.
- MIT license file.

### Changed
- Error messages für Nutzer sind nun auf Deutsch.
- CI nutzt pre-commit und cached die Umgebung.
- README neu generiert und aktualisiert.

### Fixed
- HTTP client no longer remains open between tests.

