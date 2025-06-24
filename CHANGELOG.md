# Changelog

## [Unreleased]
### Added
- Asynchronous image checks using `httpx.AsyncClient` with TTL cache.
- Error logging for failed image requests.

### Changed
- Endpoints now await image URL resolution.
- Image URL checks cached for 24 hours to improve performance.

