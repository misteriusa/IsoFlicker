from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient


def _am_signal(mod_rate: float, sample_rate: int, seconds: float) -> list[float]:
    """Generate amplitude-modulated 1 kHz tone samples."""

    t = np.arange(int(sample_rate * seconds)) / sample_rate
    carrier = np.sin(2 * np.pi * 1000 * t)
    envelope = 1 + 0.9 * np.sin(2 * np.pi * mod_rate * t)
    return (carrier * envelope).astype(np.float32).tolist()


def test_mtf_analysis_detects_modulation(client: TestClient) -> None:
    """MTF endpoint should report strong depth at commanded rates."""

    sample_rate = 48000
    segments = [
        {"mod_rate_hz": 40.0, "samples": _am_signal(40.0, sample_rate, 0.5)},
        {"mod_rate_hz": 90.0, "samples": _am_signal(90.0, sample_rate, 0.5)},
    ]
    response = client.post("/hardware/analyze/mtf", json={"sample_rate_hz": sample_rate, "segments": segments})
    assert response.status_code == 200
    data = response.json()
    assert float(data["mtf_scores"]["40"]) > 0.6
    assert data["passed_hz"] == 90.0


def test_latency_endpoint_returns_mean_and_jitter(client: TestClient) -> None:
    """Latency endpoint should detect injected offsets."""

    sample_rate = 48000
    reference = [0.0] * 128 + [1.0] + [0.0] * 127
    recordings = []
    for offset in (200, 205, 198):
        recording = [0.0] * offset + reference + [0.0] * 64
        recordings.append(recording)
    response = client.post(
        "/hardware/analyze/latency",
        json={
            "reference": reference,
            "recordings": recordings,
            "sample_rate_hz": sample_rate,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert 3.5 < payload["latency_ms"] < 5.0
    assert payload["jitter_ms"] > 0.0


def test_hardware_profile_persistence(client: TestClient) -> None:
    """Hardware profile endpoint should upsert records."""

    profile_payload = {
        "device_guid": "guid-123",
        "friendly_name": "Test Headset",
        "form_factor": "Headphones",
        "mix_format": "48000 Hz 24-bit",
        "mtf_pass_hz": 90.0,
        "mtf_scores": {"40": 0.72, "90": 0.68},
        "latency_ms": 150.0,
        "latency_jitter_ms": 12.0,
        "notes": "Synthetic test",
    }
    post_response = client.post("/hardware/profiles", json=profile_payload)
    assert post_response.status_code == 201
    created = post_response.json()
    assert created["friendly_name"] == "Test Headset"
    list_response = client.get("/hardware/profiles")
    assert list_response.status_code == 200
    rows = list_response.json()
    assert any(row["device_guid"] == "guid-123" for row in rows)
