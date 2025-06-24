from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from models import CardList, DeckCreate, Deck, GroupCreate, Group, JoinGroupRequest
import json
import os
import logging
import httpx
from cachetools import TTLCache

logger = logging.getLogger(__name__)

_image_cache: TTLCache[str, bool] = TTLCache(maxsize=256, ttl=60 * 60 * 24)

app = FastAPI(title="PTCGP Data API", version="1.0")

# CORS erlauben (z.B. für die Mobile-App)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pfade zu den Daten
base_dir = os.path.dirname(__file__)
cards_path = os.path.join(base_dir, "data", "cards.json")
sets_path = os.path.join(base_dir, "data", "sets.json")
events_path = os.path.join(base_dir, "data", "events.json")
tournaments_path = os.path.join(base_dir, "data", "tournaments.json")

if not os.path.exists(cards_path):
    raise FileNotFoundError(f"cards.json not found at {cards_path}")
if not os.path.exists(sets_path):
    raise FileNotFoundError(f"sets.json not found at {sets_path}")
if not os.path.exists(events_path):
    raise FileNotFoundError(f"events.json not found at {events_path}")
if not os.path.exists(tournaments_path):
    raise FileNotFoundError(f"tournaments.json not found at {tournaments_path}")

# Daten laden
with open(cards_path, encoding="utf-8") as f:
    _raw_cards = json.load(f)
with open(sets_path, encoding="utf-8") as f:
    _sets = {s["id"]: s for s in json.load(f)}
with open(events_path, encoding="utf-8") as f:
    _events = json.load(f)
with open(tournaments_path, encoding="utf-8") as f:
    _tournaments = json.load(f)

# In-Memory Stores für benutzergesteuerte Funktionen
_users: Dict[str, Dict[str, set]] = {}
_decks: Dict[str, Dict] = {}
_deck_counter = 1
_groups: Dict[str, Dict] = {}
_group_counter = 1

# Karten vorbereiten: globale ID und lokale ID pro Set
_cards = []
_cards_by_id = {}
_set_counter = {}
for idx, card in enumerate(_raw_cards, start=1):
    set_id = card.get("set_id")
    _set_counter[set_id] = _set_counter.get(set_id, 0) + 1
    card_obj = card.copy()
    card_obj["id"] = f"{idx:03d}"
    card_obj["_local_id"] = f"{_set_counter[set_id]:03d}"
    _cards.append(card_obj)
    _cards_by_id[card_obj["id"]] = card_obj


# Suche-Index vorbereiten
def _build_search_index(cards):
    index = {}
    for card in cards:
        per_lang = {}
        for lang in _LANGUAGES:
            name_txt = str(_filter_language(card.get("name", ""), lang)).lower()
            abil_parts = []
            for ab in card.get("abilities", []):
                abil_parts.append(
                    str(_filter_language(ab.get("name", ""), lang)).lower()
                )
                abil_parts.append(
                    str(_filter_language(ab.get("effect", ""), lang)).lower()
                )
            abil_txt = " ".join(abil_parts)
            atk_parts = []
            for at in card.get("attacks", []):
                atk_parts.append(
                    str(_filter_language(at.get("name", ""), lang)).lower()
                )
                atk_parts.append(
                    str(_filter_language(at.get("effect", ""), lang)).lower()
                )
            atk_txt = " ".join(atk_parts)
            per_lang[lang] = {
                "name": name_txt,
                "abilities": abil_txt,
                "attacks": atk_txt,
                "full": " ".join([name_txt, abil_txt, atk_txt]),
            }
        index[card["id"]] = per_lang
    return index


# Sprachenliste für Übersetzungen
_LANGUAGES = {"de", "en", "fr", "es", "it", "pt-br", "ko"}


def _filter_language(data, lang: str, default_lang: str = "de"):
    """Reduziert übersetzte Felder auf eine Sprache."""
    if isinstance(data, list):
        return [_filter_language(i, lang, default_lang) for i in data]
    if isinstance(data, dict):
        lang_keys = set(data.keys()) & _LANGUAGES
        if lang_keys:
            if lang in data:
                return _filter_language(data[lang], lang, default_lang)
            if default_lang in data:
                return _filter_language(data[default_lang], lang, default_lang)
            return _filter_language(data[next(iter(lang_keys))], lang, default_lang)
        return {k: _filter_language(v, lang, default_lang) for k, v in data.items()}
    return data


_search_index = _build_search_index(_cards)


async def _image_url(lang: str, set_id: str, local_id: str) -> str:
    """Return the best available image URL for a card.

    Performs an asynchronous HTTP ``HEAD`` request with a 3 second timeout to
    check for the existence of the high resolution image unless
    ``SKIP_IMAGE_CHECKS`` is set. Results are cached for one day.
    """

    base = f"https://assets.tcgdex.net/{lang}/tcgp/{set_id}/{local_id}"
    high = f"{base}/high.webp"
    if os.getenv("SKIP_IMAGE_CHECKS"):
        return high
    cached = _image_cache.get(high)
    if cached is not None:
        return high if cached else f"{base}/low.webp"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.head(high, timeout=3)
        ok = resp.status_code == 200
    except Exception as exc:
        logger.error("HEAD request failed for %s: %s", high, exc)
        ok = False
    _image_cache[high] = ok
    return high if ok else f"{base}/low.webp"


@app.get("/cards")
async def get_cards(
    lang: str = "de",
    set_id: Optional[str] = None,
    type_: Optional[str] = Query(None, alias="type"),
    trainer_type: Optional[str] = Query(None, alias="trainerType"),
    rarity: Optional[str] = None,
    category: Optional[str] = None,
    evolve_from: Optional[str] = None,
    stage: Optional[str] = None,
    booster: Optional[str] = None,
    illustrator: Optional[str] = None,
    suffix: Optional[str] = None,
    hp_min: Optional[int] = None,
    hp_max: Optional[int] = None,
    weakness: Optional[str] = None,
    retreat_min: Optional[int] = None,
    retreat_max: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0,
):
    """Alle Karten mit optionalen Filtern abrufen.

    Unterstützt Filter für Set, Typ, Seltenheit, Kategorie, Entwicklungsstufe,
    KP und Rückzugskosten.
    """
    result = []
    for card in _cards:
        if set_id and card.get("set_id") != set_id:
            continue
        if type_:
            card_types = card.get("types", [])
            if type_ not in card_types:
                continue
        if trainer_type and card.get("trainerType") != trainer_type:
            continue
        if rarity and card.get("rarity") != rarity:
            continue
        if category and card.get("category") != category:
            continue
        if stage and card.get("stage") != stage:
            continue
        if evolve_from:
            evo = card.get("evolveFrom")
            if not evo:
                continue
            names = evo.values() if isinstance(evo, dict) else [evo]
            if not any(str(evolve_from).lower() == str(n).lower() for n in names):
                continue
        if booster and booster not in card.get("boosters", []):
            continue
        if illustrator and card.get("illustrator") != illustrator:
            continue
        if suffix and card.get("suffix") != suffix:
            continue
        if hp_min is not None and int(card.get("hp", 0)) < hp_min:
            continue
        if hp_max is not None and int(card.get("hp", 0)) > hp_max:
            continue
        if weakness:
            weak_types = [w.get("type") for w in card.get("weaknesses", [])]
            if weakness not in weak_types:
                continue
        if retreat_min is not None and int(card.get("retreat", 0)) < retreat_min:
            continue
        if retreat_max is not None and int(card.get("retreat", 0)) > retreat_max:
            continue

        c = card.copy()
        c["set"] = _sets.get(c["set_id"])
        c["image"] = await _image_url(lang, c["set_id"], c["_local_id"])
        del c["_local_id"]
        result.append(_filter_language(c, lang))

    if offset:
        result = result[offset:]
    if limit is not None:
        result = result[:limit]
    return result


@app.get("/cards/search")
async def search_cards(
    q: str,
    lang: str = "de",
    fields: Optional[str] = Query(
        None,
        description="Komma-getrennte Liste der Felder: name, abilities, attacks",
    ),
):
    """Karten anhand eines Suchbegriffs finden."""
    results = []
    q_lower = q.lower()
    requested = None
    if fields:
        requested = [
            f.strip()
            for f in fields.split(",")
            if f.strip() in {"name", "abilities", "attacks"}
        ]
    for card in _cards:
        search_data = _search_index.get(card["id"], {}).get(lang, {})
        text = (
            search_data.get("full", "")
            if not requested
            else " ".join(search_data.get(f, "") for f in requested)
        )
        if q_lower in text:
            c = card.copy()
            c["set"] = _sets.get(c["set_id"])
            c["image"] = await _image_url(lang, c["set_id"], c["_local_id"])
            del c["_local_id"]
            results.append(_filter_language(c, lang))
    return results


@app.get("/cards/{card_id}")
async def get_card(card_id: str, lang: str = "de"):
    """Eine einzelne Karte per ID abrufen."""
    card = _cards_by_id.get(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    c = card.copy()
    c["set"] = _sets.get(c["set_id"])
    c["image"] = await _image_url(lang, c["set_id"], c["_local_id"])
    del c["_local_id"]
    return _filter_language(c, lang)


@app.get("/sets")
def get_sets(lang: str = "de"):
    """Liste aller Sets zurückgeben."""
    return [_filter_language(s, lang) for s in _sets.values()]


@app.get("/sets/{set_id}")
def get_set(set_id: str, lang: str = "de"):
    """Ein einzelnes Set abrufen."""
    s = _sets.get(set_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Set not found")
    return _filter_language(s, lang)


@app.get("/events")
def get_events():
    """Alle bekannten Events zurückgeben."""
    return _events


@app.get("/tournaments")
def get_tournaments():
    """Liste der Turniere zurückgeben."""
    return _tournaments


@app.post("/users/{user_id}/have")
def set_have(user_id: str, payload: CardList):
    """Liste der vorhandenen Karten setzen.

    Erwartet ``{"cards": [...]}`` als JSON-Body.
    """
    user = _users.setdefault(user_id, {"have": set(), "want": set()})
    user["have"] = set(payload.cards)
    return {"user": user_id, "have": sorted(user["have"])}


@app.post("/users/{user_id}/want")
def set_want(user_id: str, payload: CardList):
    """Gewünschte Karten setzen.

    Erwartet ``{"cards": [...]}`` als JSON-Body.
    """
    user = _users.setdefault(user_id, {"have": set(), "want": set()})
    user["want"] = set(payload.cards)
    return {"user": user_id, "want": sorted(user["want"])}


@app.get("/users/{user_id}")
def get_user(user_id: str):
    """Informationen zu einem Nutzer abrufen."""
    user = _users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user_id, "have": sorted(user["have"]), "want": sorted(user["want"])}


@app.get("/trades/matches")
def trade_matches():
    """Einfache Trade-Matches berechnen."""
    matches = []
    ids = list(_users.keys())
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            ua = _users[a]
            ub = _users[b]
            if ua["have"] & ub["want"] and ub["have"] & ua["want"]:
                matches.append({"user_a": a, "user_b": b})
    return matches


@app.post("/decks")
def create_deck(deck: DeckCreate) -> Deck:
    """Neues Deck anlegen.

    Erwartet ein JSON-Objekt mit ``name`` und ``cards``.
    """
    global _deck_counter
    deck_id = str(_deck_counter)
    _deck_counter += 1
    _decks[deck_id] = {
        "id": deck_id,
        "name": deck.name,
        "cards": deck.cards,
        "votes": 0,
    }
    return _decks[deck_id]


@app.get("/decks")
def list_decks():
    """Alle Decks auflisten."""
    return list(_decks.values())


@app.get("/decks/{deck_id}")
def get_deck(deck_id: str):
    """Ein Deck anhand seiner ID abrufen."""
    deck = _decks.get(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@app.post("/decks/{deck_id}/vote")
def vote_deck(deck_id: str, vote: str = Query(..., regex="^(up|down)$")) -> Deck:
    """Ein Deck positiv oder negativ bewerten."""
    deck = _decks.get(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if vote == "up":
        deck["votes"] += 1
    elif vote == "down":
        deck["votes"] -= 1
    return deck


@app.post("/groups")
def create_group(group: GroupCreate) -> Group:
    """Neue Gruppe erstellen.

    Erwartet ein JSON-Objekt mit dem Feld ``name``.
    """
    global _group_counter
    group_id = str(_group_counter)
    _group_counter += 1
    _groups[group_id] = {"id": group_id, "name": group.name, "members": []}
    return _groups[group_id]


@app.post("/groups/{group_id}/join")
def join_group(group_id: str, payload: JoinGroupRequest) -> Group:
    """Einer Gruppe beitreten.

    Erwartet ein JSON-Objekt mit ``user_id``.
    """
    group = _groups.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if payload.user_id not in group["members"]:
        group["members"].append(payload.user_id)
    return group


@app.get("/groups/{group_id}")
def get_group(group_id: str):
    """Gruppendetails abrufen."""
    group = _groups.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group
