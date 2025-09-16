"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from .config import settings
from .database import create_db_and_tables, get_session
from .presets_loader import load_preset_catalog, populate_presets
from .routers import logs, presets


def _ensure_log_directory(path: Path) -> None:
    """Create the log directory if missing."""

    path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
def lifespan(_: FastAPI):
    """Initialize database and load presets on startup."""

    create_db_and_tables()
    catalog = load_preset_catalog(settings.preset_file)
    with get_session() as session:
        populate_presets(session, catalog)
        session.commit()
    _ensure_log_directory(settings.log_directory)
    yield


app = FastAPI(title="IsoFlicker Backend", lifespan=lifespan)
app.include_router(presets.router)
app.include_router(logs.router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Simple health endpoint for monitoring."""

    return {"status": "ok"}


__all__ = ["app"]
