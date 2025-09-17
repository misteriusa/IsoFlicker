"""Pydantic/SQLModel schemas for API IO."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

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
    mechanism: Optional[str] = None
    expected_effects: str
    audio_config: dict[str, Any] = Field(default_factory=dict)
    visual_config: dict[str, Any] = Field(default_factory=dict)
    safety_label: Optional[str] = None
    safety_notes: str
    safety_config: dict[str, Any] = Field(default_factory=dict)
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


class HardwareProfileCreate(SQLModel):
    """Payload for persisting hardware detector results."""

    device_guid: str
    friendly_name: str
    form_factor: Optional[str] = None
    mix_format: Optional[str] = None
    mtf_pass_hz: Optional[float] = None
    mtf_scores: dict[str, float] = Field(default_factory=dict)
    latency_ms: Optional[float] = None
    latency_jitter_ms: Optional[float] = None
    notes: Optional[str] = None


class HardwareProfileRead(HardwareProfileCreate):
    """Response payload for stored hardware profiles."""

    id: int
    tested_at: datetime

    class Config:
        from_attributes = True


class ModulationSegment(SQLModel):
    """Recorded segment for a modulation transfer computation."""

    mod_rate_hz: float
    samples: list[float]


class MTFRequest(SQLModel):
    """Request payload for stage B acoustic analysis."""

    sample_rate_hz: int
    segments: list[ModulationSegment]


class MTFResponse(SQLModel):
    """Normalized modulation transfer scores per modulation frequency."""

    mtf_scores: dict[str, float]
    passed_hz: Optional[float]


class LatencyRequest(SQLModel):
    """Payload for acoustic latency estimation."""

    reference: list[float]
    recordings: list[list[float]]
    sample_rate_hz: int


class LatencyResponse(SQLModel):
    """Latency measurement summary."""

    latency_ms: float
    jitter_ms: float


__all__ = [
    "CategoryRead",
    "PresetRead",
    "SessionLogCreate",
    "SessionLogRead",
    "HardwareProfileCreate",
    "HardwareProfileRead",
    "MTFRequest",
    "MTFResponse",
    "LatencyRequest",
    "LatencyResponse",
]
