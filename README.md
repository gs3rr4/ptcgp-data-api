# PTCGP Data API

Eine offene FastAPI-Anwendung zum Bereitstellen von Pokémon TCG Pocket Daten.

## Voraussetzungen
- Python >= 3.12

## Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e . -r requirements-dev.txt
```

## Starten
```bash
uvicorn ptcgp_api:app --reload
```

### Railway
```bash
uvicorn ptcgp_api:app --host 0.0.0.0 --port $PORT
```

## Umgebungsvariablen
- `API_KEY` – aktiviert Schreibzugriffe mit `X-API-Key`
- `ALLOW_ORIGINS` – erlaubte CORS-Ursprünge (Standard `*`)
- `DATA_DIR` – Pfad zu den JSON-Daten (`data`)
- `IMAGE_TIMEOUT` – Timeout für Bild-Checks (Sekunden, Standard `3`)
- `LOG_LEVEL` – Detailgrad der Logs (`INFO`)
- `PROFILE_FILTERS` – Dauer der Filterung ausgeben
- `SKIP_IMAGE_CHECKS` – Bild-Prüfung deaktivieren

## Tests
```bash
pytest --cov=. --cov-report=term-missing
```
Optionale Benchmarks:
```bash
pytest --benchmark-only
```

## Endpunkte (Auswahl)
- `GET /cards` – Karten filtern
- `GET /cards/{id}` – einzelne Karte
- `GET /cards/search` – Suche in Namen, Fähigkeiten und Attacken
- `GET /sets` und `GET /sets/{id}` – Sets
- `GET /events` und `GET /tournaments`
- `POST /users/{id}/have|want` – Tauschlisten setzen
- `GET /users/{id}` – Listen abrufen
- `GET /trades/matches` – einfache Tauschempfehlungen
- `POST /decks` / `GET /decks/{id}` / `POST /decks/{id}/vote`
- `POST /groups` / `POST /groups/{id}/join` / `GET /groups/{id}`

Weitere Details siehe `CHANGELOG.md`.

## Entwicklung
Führe `pre-commit install` aus, um automatische Formatierung und Linting sicherzustellen.
Logs werden strukturiert in `logs/app.log` mit Rotationsdateien geschrieben.
Siehe `.env.example` für alle verfügbaren Umgebungsvariablen.
Der CI-Workflow führt einen Snyk-Scan nur aus, wenn ein `SNYK_TOKEN` bereitsteht
und der Pull Request aus demselben Repository stammt.

## Dependabot
Dieses Repository nutzt Dependabot, um Python-Abhängigkeiten und GitHub Actions
täglich automatisch zu aktualisieren. Jeder Dependabot-PR durchläuft die
komplette CI-Pipeline inklusive Linting, Tests und Security-Audit. Aktiviere
dazu Dependabot Alerts und Security Updates in den Repository-Einstellungen.
