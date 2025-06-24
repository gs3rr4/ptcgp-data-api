from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import os
import httpx
import logging
from cachetools import TTLCache

from ..data import (
    _cards,
    _cards_by_id,
    _sets,
    _search_index,
    filter_language,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_image_cache: TTLCache[str, bool] = TTLCache(maxsize=256, ttl=60 * 60 * 24)


async def _image_url(lang: str, set_id: str, local_id: str) -> str:
    """Return the best available image URL for a card."""
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


@router.get("/cards")
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
        result.append(filter_language(c, lang))

    if offset:
        result = result[offset:]
    if limit is not None:
        result = result[:limit]
    return result


@router.get("/cards/search")
async def search_cards(
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
            results.append(filter_language(c, lang))
    return results


@router.get("/cards/{card_id}")
async def get_card(card_id: str, lang: str = "de"):
    card = _cards_by_id.get(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    c = card.copy()
    c["set"] = _sets.get(c["set_id"])
    c["image"] = await _image_url(lang, c["set_id"], c["_local_id"])
    del c["_local_id"]
    return filter_language(c, lang)
