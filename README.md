# PTCGP Data API

Eine FastAPI-basierte REST-API für Daten aus Pokémon TCG Pocket. Die Anwendung liefert Karten-, Event- und Trading-Endpunkte.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Kopiere `.env.example` nach `.env` und passe die Variablen an.

### Server starten

```bash
uvicorn main:app --reload
```

## Tests und Linting

```bash
pre-commit run --all-files
pytest
```

Optional lassen sich Benchmarks mit `pytest --benchmark-only` ausführen.

## Sicherheitsprüfung

```bash
pip-audit -r requirements.txt -r requirements-dev.txt
```

## Umgebungsvariablen

- `LOG_LEVEL` – Log-Stufe (z. B. `DEBUG`)
- `ALLOW_ORIGINS` – erlaubte CORS-Ursprüngen
- `API_KEY` – API-Schlüssel für schreibende Endpunkte
- `SKIP_IMAGE_CHECKS` – deaktiviert Bild-Checks
- `IMAGE_TIMEOUT` – Timeout für Bild-HEAD-Requests
- `PROFILE_FILTERS` – Laufzeit der Filterung loggen
- `DATA_DIR` – Pfad zu den JSON-Daten

## Endpunkte (Auszug)

- `GET /cards` – Kartenliste mit Filtern
- `GET /cards/search` – Volltextsuche
- `GET /cards/{id}` – einzelne Karte
- `GET /sets` / `GET /sets/{id}`
- `GET /events`
- `GET /tournaments`
- `POST /users/{id}/have|want`
- `GET /users/{id}`
- `POST /decks` / `GET /decks` / `GET /decks/{id}` / `POST /decks/{id}/vote`
- `POST /groups` / `POST /groups/{id}/join` / `GET /groups/{id}`

Bei gesetztem `API_KEY` ist der Header `X-API-Key` erforderlich.

## Logging

Die Anwendung nutzt `structlog` und schreibt JSON-Logs nach `logs/app.log`. Die Log-Stufe wird über `LOG_LEVEL` gesteuert.

## Lizenz

Veröffentlicht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE).

