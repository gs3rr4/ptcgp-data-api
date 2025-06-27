"""PTCGP Data API main application.

CI checks run for every commit, including automatic Dependabot updates.
"""

import logging
import logging.handlers
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog
import httpx


from .routes import cards, users, meta

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
file_handler = logging.handlers.TimedRotatingFileHandler(
    os.path.join(LOG_DIR, "runtime.log"),
    when="H",
    interval=1,
    utc=True,
    encoding="utf-8",
)
file_handler.suffix = "%Y-%m-%d-%H.json"
file_handler.namer = lambda name: name.replace("runtime.log.", "runtime-")
logging.basicConfig(
    level=LOG_LEVEL,
    handlers=[file_handler, logging.StreamHandler()],
    format="%(message)s",
)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, LOG_LEVEL),
    ),
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger(__name__)

app = FastAPI(title="PTCGP Data API", version="1.0")

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
async def log_unhandled_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Log unhandled exceptions and return a generic error."""
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Interner Serverfehler"},
    )


@app.on_event("startup")
async def startup() -> None:
    """Initialize resources and log startup."""
    if os.getenv("API_KEY"):
        logger.info("API authentication enabled")
    app.state.http_client = httpx.AsyncClient()
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown() -> None:
    """Close resources on shutdown."""
    client: httpx.AsyncClient | None = getattr(app.state, "http_client", None)
    if client and not client.is_closed:
        await client.aclose()
