"""Tests for log endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_and_list_log(client: TestClient) -> None:
    """Posting a log should persist and then be retrievable."""

    payload = {
        "preset_id": "gamma40",
        "duration_seconds": 300.0,
        "effective_hz": 40.0,
        "jitter_p95_ms": 0.25,
        "jitter_p99_ms": 0.5,
        "dropped_frames": 0,
        "notes": "lab test",
    }
    create_response = client.post("/logs/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["preset_id"] == "gamma40"
    list_response = client.get("/logs/")
    assert list_response.status_code == 200
    entries = list_response.json()
    assert any(item["id"] == created["id"] for item in entries)
