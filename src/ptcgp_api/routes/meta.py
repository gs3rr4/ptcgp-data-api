"""Metadata routes for sets, events and tournaments."""

from fastapi import APIRouter, HTTPException

from ..data import _sets, _events, _tournaments, filter_language

router = APIRouter()


@router.get("/sets")
def get_sets(lang: str = "de"):
    """Return all sets in the requested language."""
    return [filter_language(s, lang) for s in _sets.values()]


@router.get("/sets/{set_id}")
def get_set(set_id: str, lang: str = "de"):
    """Return a single set by ID."""
    s = _sets.get(set_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Set nicht gefunden")
    return filter_language(s, lang)


@router.get("/events")
def get_events():
    """Return known events."""
    return _events


@router.get("/tournaments")
def get_tournaments():
    """Return tournament information."""
    return _tournaments
