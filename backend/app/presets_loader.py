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
    """Create or update category rows."""

    for category_id, payload in data.get("categories", {}).items():
        existing = session.exec(select(Category).where(Category.id == category_id)).first()
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


def _normalize_audio_block(raw: dict | None, fallback: dict) -> dict:
    """Return a consistent audio configuration dictionary."""

    if raw:
        return raw
    return {
        "carrier": fallback.get("type"),
        "mod_rate_hz": fallback.get("mod_rate_hz"),
        "depth": fallback.get("depth"),
        "duty": fallback.get("duty_cycle"),
        "window_ms": fallback.get("window_ms"),
    }


def _normalize_visual_block(raw: dict | None, fallback: dict) -> dict:
    """Return a consistent visual configuration dictionary."""

    merged = {k: v for k, v in (raw or {}).items() if v is not None}
    if merged:
        return merged
    return {
        "rate_hz": fallback.get("rate_hz"),
        "phase_deg": fallback.get("phase_relation_deg"),
        "contrast": fallback.get("contrast"),
    }


def _build_preset_models(raw_presets: Iterable[dict]) -> Iterable[Preset]:
    """Transform JSON dicts into Preset SQLModel instances."""

    for preset in raw_presets:
        carrier_block = preset.get("carrier") or {}
        visual_block = preset.get("visual") or {}
        audio_config = _normalize_audio_block(preset.get("audio"), {
            "type": carrier_block.get("type"),
            "mod_rate_hz": preset.get("mod_rate_hz"),
            "depth": preset.get("depth"),
            "duty_cycle": preset.get("duty_cycle"),
            "window_ms": preset.get("window_ms"),
        })
        visual_config = _normalize_visual_block(preset.get("visual_detail"), {
            "rate_hz": visual_block.get("rate_hz"),
            "phase_relation_deg": visual_block.get("phase_relation_deg"),
            "contrast": visual_block.get("contrast"),
        })
        safety_block = preset.get("safety") or {}
        yield Preset(
            id=preset["id"],
            category=preset["category"],
            label=preset.get("label", preset["id"]),
            mod_rate_hz=preset.get("mod_rate_hz"),
            duty_cycle=preset.get("duty_cycle"),
            depth=preset.get("depth"),
            window_ms=preset.get("window_ms"),
            carrier_type=carrier_block.get("type"),
            carrier_hz=carrier_block.get("carrier_hz"),
            outer_envelope_rate=(preset.get("outer_envelope") or {}).get("mod_rate_hz"),
            outer_envelope_depth=(preset.get("outer_envelope") or {}).get("depth"),
            phase_options_deg=preset.get("phase_options_deg"),
            duration_minutes=preset.get("duration_minutes"),
            visual_enabled=bool(visual_block.get("enabled")),
            visual_rate_hz=visual_block.get("rate_hz"),
            visual_phase_deg=visual_block.get("phase_relation_deg"),
            precision_note=visual_block.get("precision_note"),
            rationale=preset.get("rationale", ""),
            mechanism=preset.get("mechanism"),
            expected_effects=preset.get("expected_effects") or preset.get("expected", ""),
            audio_config=audio_config,
            visual_config=visual_config,
            safety_label=preset.get("safety_label"),
            safety_notes=safety_block.get("notes", preset.get("safety_notes", "")),
            safety_config=safety_block,
            max_volume_pct=safety_block.get("max_volume_pct"),
            photosensitivity_flag=bool(safety_block.get("photosensitivity_flag")),
            citations=[int(value) for value in preset.get("citations", [])],
        )


def populate_presets(session: Session, catalog: dict) -> None:
    """Populate presets and categories from catalog data."""

    _ensure_categories(session, catalog)
    incoming: dict[str, Preset] = {}
    for item in _build_preset_models(catalog.get("presets", [])):
        incoming[item.id] = item
    existing_ids = set(session.exec(select(Preset.id)).all())
    for preset_id, preset in incoming.items():
        if preset_id in existing_ids:
            session.merge(preset)
        else:
            session.add(preset)


__all__ = ["load_preset_catalog", "populate_presets"]
