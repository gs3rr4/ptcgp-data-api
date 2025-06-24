import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
import httpx
import structlog
from fastapi import FastAPI, Request
from logging.handlers import RotatingFileHandler
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .auth import API_KEY

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

handler = RotatingFileHandler(log_dir / "app.log", maxBytes=1_000_000, backupCount=3)

logging.basicConfig(level=LOG_LEVEL, handlers=[handler, logging.StreamHandler()])

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, LOG_LEVEL, logging.INFO)
    ),
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger(__name__)
_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    assert _client is not None
    return _client


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    _client = httpx.AsyncClient()
    if API_KEY:
        logger.info("API authentication enabled")
    logger.info("Application startup complete")
    try:
        yield
    finally:
        await _client.aclose()
        logger.info("HTTP client closed")


app = FastAPI(title="PTCGP Data API", version="1.0", lifespan=lifespan)

from .routes import cards, users, meta  # noqa: E402

allow_origins_env = os.getenv("ALLOW_ORIGINS", "*")
ALLOW_ORIGINS = (
    [o.strip() for o in allow_origins_env.split(",")]
    if allow_origins_env != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cards.router)
app.include_router(users.router)
app.include_router(meta.router)


@app.exception_handler(Exception)
async def log_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    """Log unhandled exceptions and return a generic error."""
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Interner Serverfehler"})
