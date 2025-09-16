"""SQLModel models for presets and logs."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    """Preset category metadata."""

    id: str = Field(primary_key=True, index=True)
    label: str
    description: str

class Preset(SQLModel, table=True):
    """Preset definition loaded from the default catalog."""

    id: str = Field(primary_key=True, index=True)
    category: str = Field(foreign_key="category.id")
    label: str
    mod_rate_hz: Optional[float] = Field(default=None)
    duty_cycle: Optional[float] = Field(default=None)
    depth: Optional[float] = Field(default=None)
    window_ms: Optional[float] = Field(default=None)
    carrier_type: Optional[str] = Field(default=None)
    carrier_hz: Optional[float] = Field(default=None)
    outer_envelope_rate: Optional[float] = Field(default=None)
    outer_envelope_depth: Optional[float] = Field(default=None)
    phase_options_deg: Optional[list[int]] = Field(
        sa_column=Column(JSON), default=None
    )
    duration_minutes: Optional[float] = Field(default=None)
    visual_enabled: bool = Field(default=False)
    visual_rate_hz: Optional[float] = Field(default=None)
    visual_phase_deg: Optional[float] = Field(default=None)
    precision_note: Optional[str] = Field(default=None)
    rationale: str
    expected: str
    safety_notes: str
    max_volume_pct: Optional[int] = Field(default=None)
    photosensitivity_flag: bool = Field(default=False)
    citations: list[int] = Field(sa_column=Column(JSON), default_factory=list)


class SessionLog(SQLModel, table=True):
    """Stores session telemetry summaries."""

    id: Optional[int] = Field(default=None, primary_key=True)
    preset_id: str = Field(foreign_key="preset.id")
    started_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    duration_seconds: float
    effective_hz: Optional[float] = Field(default=None)
    jitter_p95_ms: Optional[float] = Field(default=None)
    jitter_p99_ms: Optional[float] = Field(default=None)
    dropped_frames: Optional[int] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    raw_path: Optional[str] = Field(default=None)


__all__ = ["Category", "Preset", "SessionLog"]
