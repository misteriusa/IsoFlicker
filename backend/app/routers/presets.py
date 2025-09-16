"""API routes for preset catalog queries."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..database import get_session
from ..models import Category, Preset
from ..schemas import CategoryRead, PresetRead

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("/", response_model=list[PresetRead])
def list_presets(session: Session = Depends(get_session)) -> list[PresetRead]:
    """Return all presets ordered by category then label."""

    presets = session.exec(select(Preset).order_by(Preset.category, Preset.label)).all()
    return [PresetRead.model_validate(preset) for preset in presets]


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(session: Session = Depends(get_session)) -> list[CategoryRead]:
    """Return all preset categories."""

    categories = session.exec(select(Category).order_by(Category.id)).all()
    return [CategoryRead.model_validate(category) for category in categories]


@router.get("/{preset_id}", response_model=PresetRead)
def get_preset(preset_id: str, session: Session = Depends(get_session)) -> PresetRead:
    """Return a single preset by identifier or raise 404."""

    preset = session.get(Preset, preset_id)
    if preset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found")
    return PresetRead.model_validate(preset)


__all__ = ["router"]
