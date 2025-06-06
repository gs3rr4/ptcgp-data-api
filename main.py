from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# CORS erlauben (z.B. für die Mobile-App)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Richtigen Pfad zur cards.json setzen (jetzt im eigenen Repo unter data/cards.json)
cards_path = os.path.join(os.path.dirname(__file__), 'data', 'cards.json')

if not os.path.exists(cards_path):
    raise FileNotFoundError(f"cards.json not found at {cards_path}")

# Karten-Daten laden (einmalig beim Start)
with open(cards_path, encoding='utf-8') as f:
    cards = json.load(f)


@app.get("/cards")
def get_cards():
    return cards


@app.get("/cards/{card_id}")
def get_card(card_id: str):
    for card in cards:
        if card.get("id") == card_id:
            return card
    raise HTTPException(status_code=404, detail="Card not found")
