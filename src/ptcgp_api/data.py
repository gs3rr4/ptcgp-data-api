"""Load card data and build search indexes at import time."""

import json
import os
from typing import Dict, List, Any
from .models import Language


# Directory of this file -> repository root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))

CARDS_PATH = os.path.join(DATA_DIR, "cards.json")
SETS_PATH = os.path.join(DATA_DIR, "sets.json")
EVENTS_PATH = os.path.join(DATA_DIR, "events.json")
TOURNAMENTS_PATH = os.path.join(DATA_DIR, "tournaments.json")

for path in [CARDS_PATH, SETS_PATH, EVENTS_PATH, TOURNAMENTS_PATH]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required data file not found: {path}")

with open(CARDS_PATH, encoding="utf-8") as f:
    _raw_cards: List[Dict[str, Any]] = json.load(f)

with open(SETS_PATH, encoding="utf-8") as f:
    _sets: Dict[str, Dict[str, Any]] = {s["id"]: s for s in json.load(f)}

with open(EVENTS_PATH, encoding="utf-8") as f:
    _events: List[Dict[str, Any]] = json.load(f)

with open(TOURNAMENTS_PATH, encoding="utf-8") as f:
    _tournaments: List[Dict[str, Any]] = json.load(f)

# Build cards with global and local ids
_cards: List[Dict[str, Any]] = []
_cards_by_id: Dict[str, Dict[str, Any]] = {}
_index_by_set: Dict[str, set] = {}
_index_by_type: Dict[str, set] = {}
_index_by_rarity: Dict[str, set] = {}
_index_by_trainer_type: Dict[str, set] = {}

set_counter: Dict[str, int] = {}

for idx, card in enumerate(_raw_cards, start=1):
    set_id = card.get("set_id")
    set_counter[set_id] = set_counter.get(set_id, 0) + 1
    obj = card.copy()
    obj["id"] = f"{idx:03d}"
    obj["_local_id"] = f"{set_counter[set_id]:03d}"
    _cards.append(obj)
    _cards_by_id[obj["id"]] = obj

    # Build filter indexes for faster lookups
    _index_by_set.setdefault(set_id, set()).add(obj["id"])
    for t in obj.get("types", []):
        _index_by_type.setdefault(t, set()).add(obj["id"])
    if trainer_type := obj.get("trainerType"):
        _index_by_trainer_type.setdefault(trainer_type, set()).add(obj["id"])
    if rarity := obj.get("rarity"):
        _index_by_rarity.setdefault(rarity, set()).add(obj["id"])


LANGUAGES = {lang.value for lang in Language}


def filter_language(data: Any, lang: str, default_lang: str = "de") -> Any:
    """Reduce translated fields to a single language."""
    if isinstance(data, list):
        return [filter_language(i, lang, default_lang) for i in data]
    if isinstance(data, dict):
        lang_keys = set(data.keys()) & LANGUAGES
        if lang_keys:
            if lang in data:
                return filter_language(data[lang], lang, default_lang)
            if default_lang in data:
                return filter_language(data[default_lang], lang, default_lang)
            return filter_language(
                data[next(iter(lang_keys))],
                lang,
                default_lang,
            )
        filtered = {
            k: filter_language(v, lang, default_lang) for k, v in data.items()
        }  # noqa: E501
        return filtered
    return data


def build_search_index(
    cards: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Dict[str, str]]]:
    """Create a full text search index for the given cards."""
    index: Dict[str, Dict[str, Dict[str, str]]] = {}
    for card in cards:
        per_lang: Dict[str, Dict[str, str]] = {}
        for lang in LANGUAGES:
            name_txt = str(filter_language(card.get("name", ""), lang)).lower()
            abil_parts: List[str] = []
            for ab in card.get("abilities", []):
                abil_parts.append(
                    str(filter_language(ab.get("name", ""), lang)).lower()
                )
                abil_parts.append(
                    str(filter_language(ab.get("effect", ""), lang)).lower()
                )
            abil_txt = " ".join(abil_parts)
            atk_parts: List[str] = []
            for at in card.get("attacks", []):
                name_val = filter_language(at.get("name", ""), lang)
                atk_parts.append(str(name_val).lower())
                atk_parts.append(
                    str(filter_language(at.get("effect", ""), lang)).lower()
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


_search_index = build_search_index(_cards)

__all__ = [
    "_cards",
    "_cards_by_id",
    "_sets",
    "_events",
    "_tournaments",
    "_search_index",
    "_index_by_set",
    "_index_by_type",
    "_index_by_rarity",
    "_index_by_trainer_type",
    "filter_language",
    "build_search_index",
]
