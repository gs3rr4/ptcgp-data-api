from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import requests

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


def _image_url(lang: str, set_id: str, local_id: str) -> str:
    base = f"https://assets.tcgdex.net/{lang}/tcgp/{set_id}/{local_id}"
    high = f"{base}/high.webp"
    try:
        resp = requests.head(high)
        if resp.status_code == 200:
            return high
    except Exception:
        pass
    return f"{base}/low.webp"


@app.get("/cards")
def get_cards(lang: str = "de"):
    result = []
    for card in _cards:
        c = card.copy()
        c["set"] = _sets.get(c["set_id"])
        c["image"] = f"https://assets.tcgdex.net/{lang}/tcgp/{c['set_id']}/{c['_local_id']}/high.webp"
        del c["_local_id"]
        result.append(_filter_language(c, lang))
    return result


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
