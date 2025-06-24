"""Routes for user trading, decks and groups."""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict
import logging

from fastapi import Depends

from models import (
    CardList,
    DeckCreate,
    Deck,
    GroupCreate,
    Group,
    JoinGroupRequest,
    VoteDirection,
)
from ..auth import verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory stores for demo purposes
_users: Dict[str, Dict[str, set]] = {}
_decks: Dict[str, Dict] = {}
_deck_counter = 1
_groups: Dict[str, Dict] = {}
_group_counter = 1


@router.post("/users/{user_id}/have")
def set_have(user_id: str, payload: CardList, _: None = Depends(verify_api_key)):
    """Store the cards a user owns."""
    user = _users.setdefault(user_id, {"have": set(), "want": set()})
    user["have"] = set(payload.cards)
    return {"user": user_id, "have": sorted(user["have"])}


@router.post("/users/{user_id}/want")
def set_want(user_id: str, payload: CardList, _: None = Depends(verify_api_key)):
    """Store the cards a user is looking for."""
    user = _users.setdefault(user_id, {"have": set(), "want": set()})
    user["want"] = set(payload.cards)
    return {"user": user_id, "want": sorted(user["want"])}


@router.get("/users/{user_id}")
def get_user(user_id: str):
    """Return the stored card lists for a single user."""
    user = _users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user_id, "have": sorted(user["have"]), "want": sorted(user["want"])}


@router.get("/trades/matches")
def trade_matches():
    """Return simple trade suggestions between all known users."""
    matches = []
    ids = list(_users.keys())
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            ua = _users[a]
            ub = _users[b]
            if ua["have"] & ub["want"] and ub["have"] & ua["want"]:
                matches.append({"user_a": a, "user_b": b})
    return matches


@router.post("/decks")
def create_deck(deck: DeckCreate, _: None = Depends(verify_api_key)) -> Deck:
    """Create a new deck and return it."""
    global _deck_counter
    deck_id = str(_deck_counter)
    _deck_counter += 1
    _decks[deck_id] = {
        "id": deck_id,
        "name": deck.name,
        "cards": deck.cards,
        "votes": 0,
    }
    logger.info("Created deck %s with %d cards", deck_id, len(deck.cards))
    return _decks[deck_id]


@router.get("/decks")
def list_decks():
    """List all created decks."""
    return list(_decks.values())


@router.get("/decks/{deck_id}")
def get_deck(deck_id: str):
    """Return a deck by its ID."""
    deck = _decks.get(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@router.post("/decks/{deck_id}/vote")
def vote_deck(
    deck_id: str,
    vote: VoteDirection = Query(..., description="up or down"),
    _: None = Depends(verify_api_key),
) -> Deck:
    deck = _decks.get(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if vote == VoteDirection.up:
        deck["votes"] += 1
    elif vote == VoteDirection.down:
        deck["votes"] -= 1
    return deck


@router.post("/groups")
def create_group(group: GroupCreate, _: None = Depends(verify_api_key)) -> Group:
    """Create a new group and return it."""

    global _group_counter
    group_id = str(_group_counter)
    _group_counter += 1
    _groups[group_id] = {"id": group_id, "name": group.name, "members": []}
    return _groups[group_id]


@router.post("/groups/{group_id}/join")
def join_group(
    group_id: str, payload: JoinGroupRequest, _: None = Depends(verify_api_key)
) -> Group:
    """Add a user to a group."""

    group = _groups.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if payload.user_id not in group.get("members", []):
        group["members"].append(payload.user_id)
    return group


@router.get("/groups/{group_id}")
def get_group(group_id: str):
    group = _groups.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group
