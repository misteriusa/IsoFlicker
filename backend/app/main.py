"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlmodel import Session

from backend.core.config import settings
from backend.db.session import create_db_and_tables, get_engine, get_session

from .presets_loader import load_preset_catalog, populate_presets
from .routers import hardware, logs, presets


def _ensure_directory(path: Path) -> None:
    """Create directories required for runtime artifacts."""

    path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
def lifespan(_: FastAPI):
    """Initialize database, presets, and output folders on startup."""

    create_db_and_tables()
    catalog = load_preset_catalog(settings.preset_file)
    with Session(get_engine()) as session:
        populate_presets(session, catalog)
        session.commit()
    _ensure_directory(settings.log_directory)
    _ensure_directory(settings.hardware_results_dir)
    yield


app = FastAPI(title="IsoFlicker Backend", lifespan=lifespan)
app.include_router(presets.router)
app.include_router(logs.router)
app.include_router(hardware.router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Simple health endpoint for monitoring."""

    return {"status": "ok"}


__all__ = ["app"]
