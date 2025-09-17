"""Backward-compatible import shim for configuration."""
from __future__ import annotations

from backend.core.config import Settings, settings

__all__ = ["Settings", "settings"]
