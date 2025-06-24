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

### Changed
- Endpoints now await image URL resolution.
- Image URL checks cached for 24 hours to improve performance.

