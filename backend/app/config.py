"""Configuration helpers for the IsoFlicker backend."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: Annotated[str, Field(default="sqlite:///./isoflicker.db")]
    preset_file: Annotated[Path, Field(default=Path("data/presets/default_presets.json"))]
    log_directory: Annotated[Path, Field(default=Path("logs"))]

    class Config:
        env_prefix = "ISOFLICKER_"
        env_file = ".env"
        case_sensitive = False


settings = Settings()

__all__ = ["Settings", "settings"]
