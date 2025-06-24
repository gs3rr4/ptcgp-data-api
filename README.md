# PTCGP Data API

Eine einfache, offene API für Pokémon TCG Pocket Kartendaten – bereitgestellt als JSON für Bots, Mobile Apps und andere Anwendungen.

---

## Übersicht

- **API**: [https://ptcgp-api-production.up.railway.app/](https://ptcgp-api-production.up.railway.app/)
- **Datenquelle**: [ptcgp-data-extraction](https://github.com/gs3rr4/ptcgp-data-extraction)
- **Deployment**: Railway (Europa-Region)
- **Status**: Beta
- **API Version**: 1.0

---
## Lokale Entwicklung

1. Virtuelle Umgebung erstellen und aktivieren
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Abhängigkeiten installieren
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```
   Die Versionsnummern sind fest eingetragen, um reproduzierbare Umgebungen zu
   gewährleisten.
3. API lokal starten
   ```bash
   uvicorn main:app --reload
   ```
4. Tests ausführen
   ```bash
   pytest
   ```
5. Optional kann die Umgebungsvariable `SKIP_IMAGE_CHECKS=1` gesetzt werden,
   um die Prüfung von Bild-URLs (asynchroner HTTP-HEAD, Timeout 3&nbsp;s,
   zwischengespeichert für 24&nbsp;Stunden) zu überspringen.
6. Mit `IMAGE_TIMEOUT` lässt sich das Timeout für Bild-URLs in Sekunden
   konfigurieren (Standard: `3`).
7. Mit `LOG_LEVEL` kann die Ausführlichkeit der Logs gesteuert werden
   (z. B. `LOG_LEVEL=DEBUG`).
8. Mit `ALLOW_ORIGINS` lassen sich die erlaubten CORS-Ursprünge
    konfigurieren, z.&nbsp;B. `ALLOW_ORIGINS=https://example.com,https://foo.bar`.
   Standard ist `*`.
9. Für schreibende Endpunkte kann optional ein API-Key über die
    Umgebungsvariable `API_KEY` aktiviert werden. Der Client muss den gleichen
    Schlüssel im Header `X-API-Key` mitsenden.
10. Mit `DATA_DIR` kann ein alternativer Pfad zu den JSON-Daten angegeben werden.
11. Vor Commits sollte `ruff check .` ausgeführt werden, um Linting-Probleme zu
    vermeiden.

## Modulstruktur

- `main.py` – Einstiegspunkt, exportiert die FastAPI-Instanz
- `app/` – Paket mit Anwendungslogik
  - `data.py` – lädt JSON-Daten und baut den Suchindex
  - `routes/` – einzelne Router wie `cards.py` und `users.py`

---
## Logging

Das Logging kann über die Umgebungsvariable `LOG_LEVEL` angepasst werden. Der
Standardwert ist `INFO`. Bei `DEBUG` werden zusätzliche Details ausgegeben.

---
## Performance & Benchmarking

Beim Laden der Kartendaten wird nun ein Index nach Set, Typ und Seltenheit
erstellt, sodass einfache Filter deutlich schneller sind. Der Rest der
Filterung erfolgt weiter in `O(n)`.

Setze `PROFILE_FILTERS=1`, um die Laufzeit der Filterung im Log auszugeben.
Mit `pytest --benchmark-only` lassen sich optionale Benchmarks in
`tests/performance/` ausführen (erfordert `pytest-benchmark`).

---
## Authentifizierung

Ist die Umgebungsvariable `API_KEY` gesetzt, müssen Schreibzugriffe den gleichen
Schlüssel im Header `X-API-Key` mitsenden. Fehlt der Header oder stimmt der
Schlüssel nicht überein, antwortet die API mit `401 Unauthorized`.

---
## Endpunkte

### Alle Karten abrufen

`GET /cards`

- **Antwort:** Array mit Karten als JSON-Objekte
- Optionaler Query-Parameter `lang` bestimmt Sprache von Kartentext und Bild (Standard: `de`).
  Erlaubte Werte: `de`, `en`, `fr`, `es`, `it`, `pt-br`, `ko`.
- Weitere optionale Filter:
  - `set_id` – nur Karten eines bestimmten Sets
 - `type` – Pokémon-Typ
  - `trainer_type` (Alias `trainerType`) – Trainer-Typ wie `Supporter` oder `Item`
  - `rarity` – Seltenheit der Karte
  - `category` – Kategorie der Karte (z. B. `Pokemon` oder `Trainer`)
  - `stage` – Entwicklungsstufe wie `Basic`, `Stage1` oder `Stage2`
  - `evolve_from` – nur Pokémon, die sich aus dem angegebenen entwickeln
  - `booster` – Name des Boosters (muss im Feld `boosters` der Karte enthalten sein)
  - `illustrator` – Name des Illustrators
  - `suffix` – nur Karten mit bestimmtem Suffix (z. B. `EX`)
  - `hp_min` / `hp_max` – minimale bzw. maximale KP
  - `retreat_min` / `retreat_max` – minimale bzw. maximale Rückzugskosten
  - `weakness` – Schwäche-Typ der Karte
  - `limit` & `offset` – Pagination der Ergebnisse
- Ohne Angabe wird nur Deutsch zurückgegeben.
  Das hochauflösende Bild (`high.webp`) wird nur dann verwendet, wenn es
  existiert; andernfalls liefert die API `low.webp`.
  Die Prüfung erfolgt asynchron per HTTP-HEAD mit einem Timeout von `IMAGE_TIMEOUT` Sekunden (Standard 3) und wird für 24&nbsp;Stunden gecacht.
  Setze `SKIP_IMAGE_CHECKS`, um diese Prüfung zu deaktivieren und immer
  `high.webp` zu erhalten.

**Beispiele (DE/EN):**
`https://ptcgp-api-production.up.railway.app/cards?set_id=A2a&type=Metal&limit=10`
`https://ptcgp-api-production.up.railway.app/cards?lang=en&set_id=A2a&type=Metal&limit=10`

---

### Einzelne Karte abrufen

`GET /cards/{card_id}`

- `{card_id}` ist die globale ID der Karte (z. B. `002`)
- Optionaler Query-Parameter `lang` wählt Sprache von Text und Bild
- **Antwort:** JSON-Objekt der Karte inklusive Set-Informationen und Bild-URL
- Ohne Angabe wird nur Deutsch ausgegeben.
- Beispiel für Englisch: `/cards/{card_id}?lang=en`
- Das hochauflösende Bild (`high.webp`) wird nur dann verwendet, wenn es existiert.
  Die Prüfung erfolgt asynchron per HTTP-HEAD mit einem Timeout von `IMAGE_TIMEOUT` Sekunden (Standard 3) und wird für 24&nbsp;Stunden gecacht.
  Das Ergebnis der ersten Prüfung wird zwischengespeichert, um weitere Anfragen
  schneller zu beantworten.

**Beispiel:**
`https://ptcgp-api-production.up.railway.app/cards/002`

*Hinweis:* Seit einem internen Update wird beim Laden der Daten ein
zusätzlicher Index verwendet, sodass dieser Endpunkt deutlich schneller auf
eine ID-Anfrage reagieren kann.

---

### Karten suchen

`GET /cards/search`

- Query-Parameter `q` legt den Suchbegriff fest
- Optionaler Query-Parameter `lang` bestimmt Sprache von Text und Bild (Standard: `de`)
- Optionaler Query-Parameter `fields` schränkt die Suche auf bestimmte Felder ein (`name`, `abilities`, `attacks`)
- **Antwort:** Array mit Karten, die den Suchbegriff enthalten

**Beispiel:**
`GET /cards/search?q=Gift&fields=name,attacks&lang=de`

---

### Alle Sets abrufen

`GET /sets`

- Optionaler Query-Parameter `lang` bestimmt die Sprache der Setnamen (Standard: `de`)
- **Antwort:** Array mit allen Sets als JSON-Objekte

**Beispiel:**
`https://ptcgp-api-production.up.railway.app/sets`

---

### Einzelnes Set abrufen

`GET /sets/{set_id}`

- `{set_id}` ist die ID des Sets (z. B. `A2a`)
- Optionaler Query-Parameter `lang` wählt die Sprache der Felder
- **Antwort:** JSON-Objekt des Sets
- Bei unbekannter ID wird `404` zurückgegeben.

**Beispiel:**
`https://ptcgp-api-production.up.railway.app/sets/A2a`

---

### Events abrufen

`GET /events`

- **Antwort:** Array mit bekannten Events

**Beispiel:**
`https://ptcgp-api-production.up.railway.app/events`

---

### Turniere abrufen

`GET /tournaments`

- **Antwort:** Array mit Turnierinformationen

**Beispiel:**
`https://ptcgp-api-production.up.railway.app/tournaments`

---

### Trading-Funktionen

- `POST /users/{id}/have` – setzt Karten, die ein Nutzer anbietet
- `POST /users/{id}/want` – setzt Karten, die ein Nutzer sucht
- `GET /users/{id}` – gibt die aktuellen Listen eines Nutzers zurück
- `GET /trades/matches` – listet einfache Tauschvorschläge zwischen Nutzern

**Beispiel:**

```json
{
  "cards": ["001", "002"]
}
```

### Deck-Verwaltung

- `POST /decks` – neues Deck anlegen (`name`, `cards`)
- `GET /decks` – alle Decks abrufen
- `GET /decks/{deck_id}` – einzelnes Deck anzeigen
- `POST /decks/{deck_id}/vote` – Deck bewerten (`vote=up|down`)

**Beispiel für POST /decks:**

```json
{
  "name": "Test Deck",
  "cards": ["001"]
}
```

### Godpack-Gruppen

- `POST /groups` – neue Gruppe anlegen (`name`)
- `POST /groups/{group_id}/join` – Gruppe beitreten (`user_id`)
- `GET /groups/{group_id}` – Gruppendetails abrufen

**Beispiel für POST /groups:**

```json
{
  "name": "Test Group"
}
```

**Beispiel für POST /groups/{group_id}/join:**

```json
{
  "user_id": "alice"
}
```

---

## Beispielantwort


```json
{
  "id": "002",
  "name": "Beispielkarte",
  "set": {
    "id": "A2a",
    "name": "Licht des Triumphs",
    "releaseDate": "2025-02-28"
  },
  "image": "https://assets.tcgdex.net/de/tcgp/A2a/002/high.webp"
  // weitere Felder wie illustrator, rarity, attacks, ...
}
```
---

## Nutzung

- **Discord Bot:** Direktes Laden der Kartendaten über die API
- **Mobile App:** Konsumiert die API, um Kartendetails, Suchfunktionen etc. bereitzustellen
- **Weitere Ideen:** Anbindung an Webseiten, weitere Bots, Visualisierungen etc.

---

## Lizenz & Hinweise

- Die Daten stammen aus [tcgdex/cards-database](https://github.com/tcgdex/cards-database)
- Dieses Projekt extrahiert, vereinheitlicht und stellt die Daten für eigene Community-Zwecke bereit.
- **Keine kommerzielle Nutzung** ohne Genehmigung der Rechteinhaber.

---

## Kontakt & Support

- Entwickler: Gerrit (gs3rr4)
- Discord: Lotus Gaming

---

**Letztes Update:** 2025-06-25
