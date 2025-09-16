"""Pytest fixtures for the IsoFlicker backend."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.database import configure_engine, create_db_and_tables, get_session
from backend.app.main import app
from backend.app.presets_loader import load_preset_catalog, populate_presets


@pytest.fixture(scope="function", autouse=True)
def _reset_db(tmp_path: Path) -> Iterator[None]:
    """Configure an isolated SQLite database per test."""

    db_path = tmp_path / "test.db"
    configure_engine(f"sqlite:///{db_path}")
    create_db_and_tables()
    catalog = load_preset_catalog(settings.preset_file)
    session_gen = get_session()
    session = next(session_gen)
    try:
        populate_presets(session, catalog)
        session.commit()
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass
    yield


@pytest.fixture()
def client() -> TestClient:
    """Return a FastAPI test client."""

    return TestClient(app)
