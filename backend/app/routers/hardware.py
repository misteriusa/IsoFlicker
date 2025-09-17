"""Hardware detector API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import desc
from sqlmodel import Session, select

from ..database import get_session
from ..models import HardwareProfile
from ..schemas import (
    HardwareProfileCreate,
    HardwareProfileRead,
    LatencyRequest,
    LatencyResponse,
    MTFRequest,
    MTFResponse,
)
from ..services.hardware_analysis import compute_mtf, estimate_latency

router = APIRouter(prefix="/hardware", tags=["hardware"])


@router.post("/analyze/mtf", response_model=MTFResponse)
def analyze_mtf(payload: MTFRequest) -> MTFResponse:
    """Compute normalized modulation transfer scores."""

    segments = [(segment.mod_rate_hz, segment.samples) for segment in payload.segments]
    scores, passed = compute_mtf(payload.sample_rate_hz, segments)
    return MTFResponse(mtf_scores=scores, passed_hz=passed)


@router.post("/analyze/latency", response_model=LatencyResponse)
def analyze_latency(payload: LatencyRequest) -> LatencyResponse:
    """Estimate playback latency and jitter in milliseconds."""

    latency_ms, jitter_ms = estimate_latency(payload.reference, payload.recordings, payload.sample_rate_hz)
    return LatencyResponse(latency_ms=latency_ms, jitter_ms=jitter_ms)


@router.post("/profiles", response_model=HardwareProfileRead, status_code=status.HTTP_201_CREATED)
def upsert_profile(
    payload: HardwareProfileCreate,
    session: Session = Depends(get_session),
) -> HardwareProfileRead:
    """Create or update a hardware detector profile."""

    existing = session.exec(
        select(HardwareProfile).where(HardwareProfile.device_guid == payload.device_guid)
    ).first()
    data = payload.model_dump()
    if existing:
        for field, value in data.items():
            setattr(existing, field, value)
        profile = existing
    else:
        profile = HardwareProfile(**data)
        session.add(profile)
    session.commit()
    session.refresh(profile)
    return HardwareProfileRead.model_validate(profile)


@router.get("/profiles", response_model=list[HardwareProfileRead])
def list_profiles(session: Session = Depends(get_session)) -> list[HardwareProfileRead]:
    """Return known hardware detector profiles ordered by recency."""

    tested_at_col = HardwareProfile.__table__.c.tested_at  # type: ignore[attr-defined]
    rows = session.exec(select(HardwareProfile).order_by(desc(tested_at_col))).all()
    return [HardwareProfileRead.model_validate(row) for row in rows]


__all__ = ["router"]
