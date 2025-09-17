"""SQLModel session helpers."""
from __future__ import annotations

from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from backend.core.config import settings

_engine = create_engine(settings.database_url, echo=False, future=True)


def configure_engine(database_url: str) -> None:
    """Recreate the SQLModel engine (used by tests and CLI)."""

    global _engine
    _engine = create_engine(database_url, echo=False, future=True)


def get_engine():
    """Return the configured SQLModel engine."""

    return _engine


def create_db_and_tables() -> None:
    """Create SQLModel tables when they do not yet exist."""

    SQLModel.metadata.create_all(get_engine())


def get_session() -> Iterator[Session]:
    """Yield a SQLModel session with automatic close."""

    with Session(get_engine()) as session:
        yield session


__all__ = [
    "configure_engine",
    "create_db_and_tables",
    "get_engine",
    "get_session",
]
