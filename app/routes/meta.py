from fastapi import APIRouter, HTTPException

from ..data import _sets, _events, _tournaments, filter_language

router = APIRouter()


@router.get("/sets")
def get_sets(lang: str = "de"):
    return [filter_language(s, lang) for s in _sets.values()]


@router.get("/sets/{set_id}")
def get_set(set_id: str, lang: str = "de"):
    s = _sets.get(set_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Set not found")
    return filter_language(s, lang)


@router.get("/events")
def get_events():
    return _events


@router.get("/tournaments")
def get_tournaments():
    return _tournaments
