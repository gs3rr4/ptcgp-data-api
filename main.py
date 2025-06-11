from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json
import os
import requests

_image_cache = {}

app = FastAPI()

# CORS erlauben (z.B. für die Mobile-App)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pfade zu den Daten
base_dir = os.path.dirname(__file__)
cards_path = os.path.join(base_dir, 'data', 'cards.json')
sets_path = os.path.join(base_dir, 'data', 'sets.json')

if not os.path.exists(cards_path):
    raise FileNotFoundError(f"cards.json not found at {cards_path}")
if not os.path.exists(sets_path):
    raise FileNotFoundError(f"sets.json not found at {sets_path}")

# Daten laden
with open(cards_path, encoding='utf-8') as f:
    _raw_cards = json.load(f)
with open(sets_path, encoding='utf-8') as f:
    _sets = {s["id"]: s for s in json.load(f)}

# Karten vorbereiten: globale ID und lokale ID pro Set
_cards = []
_set_counter = {}
for idx, card in enumerate(_raw_cards, start=1):
    set_id = card.get("set_id")
    _set_counter[set_id] = _set_counter.get(set_id, 0) + 1
    card_obj = card.copy()
    card_obj["id"] = f"{idx:03d}"
    card_obj["_local_id"] = f"{_set_counter[set_id]:03d}"
    _cards.append(card_obj)


# Suche-Index vorbereiten
def _build_search_index(cards):
    index = {}
    for card in cards:
        per_lang = {}
        for lang in _LANGUAGES:
            name_txt = str(_filter_language(card.get("name", ""), lang)).lower()
            abil_parts = []
            for ab in card.get("abilities", []):
                abil_parts.append(str(_filter_language(ab.get("name", ""), lang)).lower())
                abil_parts.append(str(_filter_language(ab.get("effect", ""), lang)).lower())
            abil_txt = " ".join(abil_parts)
            atk_parts = []
            for at in card.get("attacks", []):
                atk_parts.append(str(_filter_language(at.get("name", ""), lang)).lower())
                atk_parts.append(str(_filter_language(at.get("effect", ""), lang)).lower())
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

_search_index = _build_search_index(_cards)


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


def _image_url(lang: str, set_id: str, local_id: str) -> str:
    base = f"https://assets.tcgdex.net/{lang}/tcgp/{set_id}/{local_id}"
    high = f"{base}/high.webp"
    if high not in _image_cache:
        try:
            resp = requests.head(high)
            _image_cache[high] = resp.status_code == 200
        except Exception:
            _image_cache[high] = False
    if _image_cache[high]:
        return high
    return f"{base}/low.webp"


@app.get("/cards")
def get_cards(
    lang: str = "de",
    set_id: Optional[str] = None,
    type_: Optional[str] = Query(None, alias="type"),
    trainer_type: Optional[str] = Query(None, alias="trainerType"),
    rarity: Optional[str] = None,
    category: Optional[str] = None,
    booster: Optional[str] = None,
    illustrator: Optional[str] = None,
    suffix: Optional[str] = None,
    hp_min: Optional[int] = None,
    hp_max: Optional[int] = None,
    retreat_min: Optional[int] = None,
    retreat_max: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0,
):
    """Alle Karten mit optionalen Filtern abrufen.

    Unterstützt Filter für Set, Typ, Seltenheit, Kategorie, KP und
    Rückzugskosten.
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
        if booster and booster not in card.get("boosters", []):
        if illustrator and card.get("illustrator") != illustrator:
        if suffix and card.get("suffix") != suffix:
            continue
        if hp_min is not None and int(card.get("hp", 0)) < hp_min:
            continue
        if hp_max is not None and int(card.get("hp", 0)) > hp_max:
            continue
        if retreat_min is not None and int(card.get("retreat", 0)) < retreat_min:
            continue
        if retreat_max is not None and int(card.get("retreat", 0)) > retreat_max:
            continue

        c = card.copy()
        c["set"] = _sets.get(c["set_id"])
        c["image"] = f"https://assets.tcgdex.net/{lang}/tcgp/{c['set_id']}/{c['_local_id']}/high.webp"
        del c["_local_id"]
        result.append(_filter_language(c, lang))

    if offset:
        result = result[offset:]
    if limit is not None:
        result = result[:limit]
    return result


@app.get("/cards/search")
def search_cards(
    q: str,
    lang: str = "de",
    fields: Optional[str] = Query(
        None,
        description="Komma-getrennte Liste der Felder: name, abilities, attacks",
    ),
):
    results = []
    q_lower = q.lower()
    requested = None
    if fields:
        requested = [f.strip() for f in fields.split(",") if f.strip() in {"name", "abilities", "attacks"}]
    for card in _cards:
        search_data = _search_index.get(card["id"], {}).get(lang, {})
        text = search_data.get("full", "") if not requested else " ".join(
            search_data.get(f, "") for f in requested
        )
        if q_lower in text:
            c = card.copy()
            c["set"] = _sets.get(c["set_id"])
            c["image"] = f"https://assets.tcgdex.net/{lang}/tcgp/{c['set_id']}/{c['_local_id']}/high.webp"
            del c["_local_id"]
            results.append(_filter_language(c, lang))
    return results


@app.get("/cards/{card_id}")
def get_card(card_id: str, lang: str = "de"):
    for card in _cards:
        if card["id"] == card_id:
            c = card.copy()
            c["set"] = _sets.get(c["set_id"])
            c["image"] = _image_url(lang, c["set_id"], c["_local_id"])
            del c["_local_id"]
            return _filter_language(c, lang)
    raise HTTPException(status_code=404, detail="Card not found")


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
