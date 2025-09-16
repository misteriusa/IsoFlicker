"""Pydantic/SQLModel schemas for API IO."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class CategoryRead(SQLModel):
    """API representation of a category."""

    id: str
    label: str
    description: str


class PresetRead(SQLModel):
    """API representation of a preset."""

    id: str
    category: str
    label: str
    mod_rate_hz: Optional[float] = None
    duty_cycle: Optional[float] = None
    depth: Optional[float] = None
    window_ms: Optional[float] = None
    carrier_type: Optional[str] = None
    carrier_hz: Optional[float] = None
    outer_envelope_rate: Optional[float] = None
    outer_envelope_depth: Optional[float] = None
    phase_options_deg: Optional[list[int]] = None
    duration_minutes: Optional[float] = None
    visual_enabled: bool = False
    visual_rate_hz: Optional[float] = None
    visual_phase_deg: Optional[float] = None
    precision_note: Optional[str] = None
    rationale: str
    expected: str
    safety_notes: str
    max_volume_pct: Optional[int] = None
    photosensitivity_flag: bool = False
    citations: list[int] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SessionLogCreate(SQLModel):
    """Schema used when uploading a new session log summary."""

    preset_id: str
    duration_seconds: float
    effective_hz: Optional[float] = None
    jitter_p95_ms: Optional[float] = None
    jitter_p99_ms: Optional[float] = None
    dropped_frames: Optional[int] = None
    notes: Optional[str] = None
    raw_path: Optional[str] = None


class SessionLogRead(SessionLogCreate):
    """Session log response payload."""

    id: int
    started_at: datetime

    class Config:
        from_attributes = True


__all__ = [
    "CategoryRead",
    "PresetRead",
    "SessionLogCreate",
    "SessionLogRead",
]
