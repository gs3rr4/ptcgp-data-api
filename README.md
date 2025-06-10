# PTCGP Data API

Eine einfache, offene API für Pokémon TCG Pocket Kartendaten – bereitgestellt als JSON für Bots, Mobile Apps und andere Anwendungen.

---

## Übersicht

- **API**: [https://ptcgp-api-production.up.railway.app/](https://ptcgp-api-production.up.railway.app/)
- **Datenquelle**: [ptcgp-data-extraction](https://github.com/gs3rr4/ptcgp-data-extraction)
- **Deployment**: Railway (Europa-Region)
- **Status**: Beta

---
## Lokale Entwicklung

1. Virtuelle Umgebung erstellen und aktivieren
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Abhängigkeiten installieren
   ```bash
   pip install -r requirements.txt
   ```
3. API lokal starten
   ```bash
   uvicorn main:app --reload
   ```

---
## Endpunkte

### Alle Karten abrufen

`GET /cards`

- **Antwort:** Array mit Karten als JSON-Objekte
- Optionaler Query-Parameter `lang` bestimmt Sprache von Kartentext und Bild (Standard: `de`)
- Weitere optionale Filter:
  - `set_id` – nur Karten eines bestimmten Sets
  - `type` – Pokémon-Typ oder Trainer-Typ
  - `rarity` – Seltenheit der Karte
  - `hp_min` / `hp_max` – minimale bzw. maximale KP
  - `limit` & `offset` – Pagination der Ergebnisse
- Ohne Angabe wird nur Deutsch zurückgegeben.
- Beispiel für Englisch: `/cards?lang=en`
- Beispiel mit Filtern: `/cards?set_id=A2a&type=Metal&hp_min=100&limit=10`

**Beispiel:**
`https://ptcgp-api-production.up.railway.app/cards`

---

### Einzelne Karte abrufen

`GET /cards/{card_id}`

- `{card_id}` ist die globale ID der Karte (z. B. `002`)
- Optionaler Query-Parameter `lang` wählt Sprache von Text und Bild
- **Antwort:** JSON-Objekt der Karte inklusive Set-Informationen und Bild-URL
- Ohne Angabe wird nur Deutsch ausgegeben.
- Beispiel für Englisch: `/cards/{card_id}?lang=en`

**Beispiel:**
`https://ptcgp-api-production.up.railway.app/cards/002`

---

### Karten suchen

`GET /cards/search`

- Query-Parameter `q` legt den Suchbegriff fest
- Optionaler Query-Parameter `lang` bestimmt Sprache von Text und Bild (Standard: `de`)
- **Antwort:** Array mit Karten, die den Suchbegriff enthalten

**Beispiel:**
`GET /cards/search?q=Gift&lang=de`

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

**Letztes Update:** 2025-06-07
