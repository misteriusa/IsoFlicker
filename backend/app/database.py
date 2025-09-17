"""Backward-compatible import shim for database helpers."""
from __future__ import annotations

from backend.db.session import (
    configure_engine,
    create_db_and_tables,
    get_engine,
    get_session,
)

__all__ = [
    "configure_engine",
    "create_db_and_tables",
    "get_engine",
    "get_session",
]
