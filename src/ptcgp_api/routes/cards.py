"""Routes for card data and search operations."""

from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional
import os
import structlog
import time
from cachetools import TTLCache
import httpx

from ..data import (
    _cards,
    _cards_by_id,
    _sets,
    _search_index,
    _index_by_set,
    _index_by_type,
    _index_by_rarity,
    _index_by_trainer_type,
    filter_language,
)
from ..models import Language

logger = structlog.get_logger(__name__)
router = APIRouter()

IMAGE_TIMEOUT = float(os.getenv("IMAGE_TIMEOUT", "3"))
_image_cache: TTLCache[str, bool] = TTLCache(maxsize=256, ttl=60 * 60 * 24)


async def _image_url(
    client: httpx.AsyncClient, lang: Language | str, set_id: str, local_id: str
) -> str:
    """Return the best available image URL for a card."""
    lang_val = lang.value if isinstance(lang, Language) else lang
    base = f"https://assets.tcgdex.net/{lang_val}/tcgp/{set_id}/{local_id}"
    high = f"{base}/high.webp"
    if os.getenv("SKIP_IMAGE_CHECKS"):
        return high
    cached = _image_cache.get(high)
    if cached is not None:
        return high if cached else f"{base}/low.webp"
    ok = False
    for attempt in range(2):
        try:
            resp = await client.head(high, timeout=IMAGE_TIMEOUT)
            ok = resp.status_code == 200
            if ok:
                break
        except Exception as exc:
            logger.error("HEAD request failed for %s: %s", high, exc)
        if attempt == 0 and not ok:
            logger.debug("Retrying image HEAD request for %s", high)
    _image_cache[high] = ok
    return high if ok else f"{base}/low.webp"


@router.get("/cards")
async def get_cards(
    request: Request,
    lang: Language = Language.de,
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
    """Return cards filtered by query parameters.

    The initial filtering by ``set_id``, ``type`` and ``rarity`` uses
    pre-built indexes for ``O(k)`` lookups. Remaining filters are applied
    with an ``O(n)`` scan over the candidate set.
    """
    start_ts = time.perf_counter() if os.getenv("PROFILE_FILTERS") else None
    logger.info("get_cards request lang=%s set_id=%s", lang, set_id)

    candidate_ids: Optional[set] = None
    if set_id:
        candidate_ids = set(_index_by_set.get(set_id, set()))
    if type_:
        ids = _index_by_type.get(type_, set())
        candidate_ids = ids if candidate_ids is None else candidate_ids & ids
    if trainer_type:
        ids = _index_by_trainer_type.get(trainer_type, set())
        candidate_ids = ids if candidate_ids is None else candidate_ids & ids
    if rarity:
        ids = _index_by_rarity.get(rarity, set())
        candidate_ids = ids if candidate_ids is None else candidate_ids & ids

    search_space = (
        _cards
        if candidate_ids is None
        else [c for c in _cards if c["id"] in candidate_ids]
    )

    result = []
    for card in search_space:
        if category and card.get("category") != category:
            continue
        if stage and card.get("stage") != stage:
            continue
        if evolve_from:
            evo = card.get("evolveFrom")
            if not evo:
                continue
            names = evo.values() if isinstance(evo, dict) else [evo]
            if not any(
                str(evolve_from).lower() == str(n).lower() for n in names
            ):  # noqa: E501
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
        if (
            retreat_min is not None
            and int(card.get("retreat", 0)) < retreat_min  # noqa: E501
        ):
            continue
        if (
            retreat_max is not None
            and int(card.get("retreat", 0)) > retreat_max  # noqa: E501
        ):
            continue

        c = card.copy()
        c["set"] = _sets.get(c["set_id"])
        c["image"] = await _image_url(
            request.app.state.http_client, lang, c["set_id"], c["_local_id"]
        )
        del c["_local_id"]
        result.append(filter_language(c, lang))

    if offset:
        result = result[offset:]
    if limit is not None:
        result = result[:limit]
    if start_ts is not None:
        logger.info(
            "get_cards filtered %d cards in %.4fs",
            len(result),
            time.perf_counter() - start_ts,
        )
    return result


@router.get("/cards/search")
async def search_cards(
    request: Request,
    q: str,
    lang: Language = Language.de,
    fields: Optional[str] = Query(
        None,
        description=(
            "Komma-getrennte Liste der Felder: name, abilities, attacks"
        ),  # noqa: E501
    ),
):
    """Search cards by query string and optional fields."""
    logger.info("search_cards q=%s lang=%s", q, lang)
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
        search_data = _search_index.get(card["id"], {}).get(
            lang.value if isinstance(lang, Language) else lang,
            {},
        )
        text = (
            search_data.get("full", "")
            if not requested
            else " ".join(search_data.get(f, "") for f in requested)
        )
        if q_lower in text:
            c = card.copy()
            c["set"] = _sets.get(c["set_id"])
            c["image"] = await _image_url(
                request.app.state.http_client,
                lang,
                c["set_id"],
                c["_local_id"],
            )
            del c["_local_id"]
            results.append(filter_language(c, lang))
    return results


@router.get("/cards/{card_id}")
async def get_card(
    request: Request,
    card_id: str,
    lang: Language = Language.de,
):
    card = _cards_by_id.get(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Karte nicht gefunden")
    c = card.copy()
    c["set"] = _sets.get(c["set_id"])
    c["image"] = await _image_url(
        request.app.state.http_client, lang, c["set_id"], c["_local_id"]
    )
    del c["_local_id"]
    return filter_language(c, lang)
