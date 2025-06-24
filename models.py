from typing import List
from pydantic import BaseModel, Field


class CardList(BaseModel):
    """List of card IDs."""

    cards: List[str] = Field(..., example=["001", "002"])


class DeckCreate(BaseModel):
    """Payload for creating a deck."""

    name: str = Field(..., example="My Deck")
    cards: List[str] = Field(..., example=["001", "002"])


class Deck(DeckCreate):
    """Deck with ID and vote counter."""

    id: str
    votes: int


class GroupCreate(BaseModel):
    """Payload for creating a group."""

    name: str = Field(..., example="My Group")


class Group(BaseModel):
    """Group representation."""

    id: str
    name: str
    members: List[str] = Field(default_factory=list)


class JoinGroupRequest(BaseModel):
    """Payload for joining a group."""

    user_id: str = Field(..., example="alice")
