"""Application configuration loaded from environment variables."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Strongly typed application settings."""

    database_url: Annotated[str, Field(default="sqlite:///./isoflicker.db")]
    preset_file: Annotated[Path, Field(default=Path("data/presets/default_presets.json"))]
    log_directory: Annotated[Path, Field(default=Path("logs"))]
    hardware_results_dir: Annotated[Path, Field(default=Path("data/hardware"))]
    mtf_pass_threshold: Annotated[float, Field(default=0.6, ge=0.0, le=1.0)]

    class Config:
        env_prefix = "ISOFLICKER_"
        env_file = ".env"
        case_sensitive = False


settings = Settings()  # type: ignore[call-arg]

__all__ = ["Settings", "settings"]
