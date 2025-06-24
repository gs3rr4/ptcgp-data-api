from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import cards, users, meta

app = FastAPI(title="PTCGP Data API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cards.router)
app.include_router(users.router)
app.include_router(meta.router)
