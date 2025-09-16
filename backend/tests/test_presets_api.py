"""Tests for preset endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_presets_returns_catalog(client: TestClient) -> None:
    """Ensure the preset list endpoint returns the seeded catalog."""

    response = client.get("/presets/")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    # There should be at least one entry for each category.
    categories = {item["category"] for item in payload}
    assert {"A", "B"}.issubset(categories)


def test_get_preset_returns_detail(client: TestClient) -> None:
    """Fetch a known preset and verify key fields."""

    response = client.get("/presets/gamma40")
    assert response.status_code == 200
    data = response.json()
    assert data["label"].lower().startswith("gamma")
    assert data["visual_enabled"] is True
    assert data["rationale"]


def test_list_categories(client: TestClient) -> None:
    """Ensure categories endpoint returns metadata."""

    response = client.get("/presets/categories")
    assert response.status_code == 200
    data = response.json()
    assert any(item["id"] == "A" for item in data)
    assert any(item["id"] == "B" for item in data)
