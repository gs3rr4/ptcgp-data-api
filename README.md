# PTCGP Data API

Eine einfache, offene API für Pokémon TCG Pocket Kartendaten – bereitgestellt als JSON für Bots, Mobile Apps und andere Anwendungen.

---

## Übersicht

- **API**: [https://ptcgp-api-production.up.railway.app/](https://ptcgp-api-production.up.railway.app/)
- **Datenquelle**: [ptcgp-data-extraction](https://github.com/gs3rr4/ptcgp-data-extraction)
- **Deployment**: Railway (Europa-Region)
- **Status**: Beta

---

## Endpunkte

### Alle Karten abrufen

`GET /cards`

- **Antwort:** Array mit allen Karten als JSON-Objekte

**Beispiel:**  
`https://ptcgp-api-production.up.railway.app/cards`

---

### Einzelne Karte abrufen

`GET /cards/{card_id}`

- `{card_id}` ist die eindeutige ID der Karte (z. B. “002”)
- **Antwort:** JSON-Objekt der Karte

**Beispiel:**  
`https://ptcgp-api-production.up.railway.app/cards/002`

---

## Beispielantwort

```json
[
  {
    "id": "002",
    "name": {
      "en": "Burmy",
      "de": "Burmy"
      // weitere Sprachen…
    },
    "set": {
      "id": "A2a",
      "name": {
        "en": "Triumphant Light",
        "de": "Licht des Triumphs"
      }
    }
    // weitere Felder wie illustrator, rarity, attacks, usw.
  }
  // weitere Karten
]
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

**Letztes Update:** 2025-06-06
