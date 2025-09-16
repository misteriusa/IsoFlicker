"""Database helpers for SQLModel."""
from __future__ import annotations

from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from .config import settings

_engine = create_engine(settings.database_url, echo=False, future=True)


def configure_engine(database_url: str) -> None:
    """Recreate the SQLModel engine (useful for tests)."""

    global _engine
    _engine = create_engine(database_url, echo=False, future=True)


def get_engine():
    """Return the active SQLModel engine."""

    return _engine


def create_db_and_tables() -> None:
    """Create all SQLModel tables if they do not already exist."""

    SQLModel.metadata.create_all(get_engine())


def get_session() -> Iterator[Session]:
    """Yield a SQLModel session with automatic closing."""

    with Session(get_engine()) as session:
        yield session


__all__ = [
    "configure_engine",
    "create_db_and_tables",
    "get_session",
    "get_engine",
]
