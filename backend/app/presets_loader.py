"""Utilities for loading preset metadata into the database."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from sqlmodel import Session, select

from .models import Category, Preset


def load_preset_catalog(path: Path) -> dict:
    """Load the preset catalog JSON file."""

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _ensure_categories(session: Session, data: dict) -> None:
    """Create category rows when missing."""

    for category_id, payload in data.get("categories", {}).items():
        existing = session.exec(
            select(Category).where(Category.id == category_id)
        ).first()
        if existing:
            existing.label = payload.get("label", existing.label)
            existing.description = payload.get("description", existing.description)
            continue
        session.add(
            Category(
                id=category_id,
                label=payload.get("label", category_id),
                description=payload.get("description", ""),
            )
        )


def _build_preset_models(raw_presets: Iterable[dict]) -> Iterable[Preset]:
    """Transform JSON dicts into Preset SQLModel instances."""

    for preset in raw_presets:
        outer = preset.get("outer_envelope") or {}
        visual = preset.get("visual") or {}
        yield Preset(
            id=preset["id"],
            category=preset["category"],
            label=preset.get("label", preset["id"]),
            mod_rate_hz=preset.get("mod_rate_hz"),
            duty_cycle=preset.get("duty_cycle"),
            depth=preset.get("depth"),
            window_ms=preset.get("window_ms"),
            carrier_type=(preset.get("carrier") or {}).get("type"),
            carrier_hz=(preset.get("carrier") or {}).get("carrier_hz"),
            outer_envelope_rate=outer.get("mod_rate_hz"),
            outer_envelope_depth=outer.get("depth"),
            phase_options_deg=preset.get("phase_options_deg"),
            duration_minutes=preset.get("duration_minutes"),
            visual_enabled=bool(visual.get("enabled")),
            visual_rate_hz=visual.get("rate_hz"),
            visual_phase_deg=visual.get("phase_relation_deg"),
            precision_note=visual.get("precision_note"),
            rationale=preset.get("rationale", ""),
            expected=preset.get("expected", ""),
            safety_notes=(preset.get("safety") or {}).get("notes", ""),
            max_volume_pct=(preset.get("safety") or {}).get("max_volume_pct"),
            photosensitivity_flag=bool((preset.get("safety") or {}).get("photosensitivity_flag")),
            citations=preset.get("citations", []),
        )


def populate_presets(session: Session, catalog: dict) -> None:
    """Populate presets and categories from catalog data."""

    _ensure_categories(session, catalog)
    incoming = {item.id: item for item in _build_preset_models(catalog.get("presets", []))}
    existing_ids = {
        preset.id for preset in session.exec(select(Preset.id)).all()
    }
    for preset_id, preset in incoming.items():
        if preset_id in existing_ids:
            session.merge(preset)
        else:
            session.add(preset)


__all__ = ["load_preset_catalog", "populate_presets"]
