"""Signal-processing helpers for the hardware detector."""
from __future__ import annotations

from typing import Iterable

import numpy as np
from numpy.typing import NDArray
from scipy.signal import hilbert, correlate  # type: ignore[import-untyped]

from backend.core.config import settings


def _to_array(samples: Iterable[float]) -> NDArray[np.float64]:
    """Convert an iterable of floats to a numpy array."""

    return np.asarray(list(samples), dtype=np.float64)


def _normalized_depth(envelope: NDArray[np.float64], sample_rate: int, target_hz: float) -> float:
    """Compute modulation depth using Hilbert envelope and FFT ratio."""

    window = np.hanning(len(envelope))
    spectrum = np.fft.rfft(envelope * window)
    freqs = np.fft.rfftfreq(len(envelope), d=1.0 / sample_rate)
    idx = int(np.argmin(np.abs(freqs - target_hz)))
    mod_amp = float(np.abs(spectrum[idx]))
    dc_amp = float(np.abs(spectrum[0])) or 1e-9
    return float(np.clip(mod_amp / dc_amp, 0.0, 1.0))


def compute_mtf(sample_rate: int, segments: Iterable[tuple[float, Iterable[float]]]) -> tuple[dict[str, float], float | None]:
    """Return normalized modulation transfer scores and highest passing rate."""

    scores: dict[str, float] = {}
    for mod_rate, samples in segments:
        data = _to_array(samples)
        if data.size < sample_rate // 4:
            scores[f"{mod_rate:.0f}"] = 0.0
            continue
        envelope = np.abs(hilbert(data))
        envelope -= np.mean(envelope)
        score = _normalized_depth(envelope, sample_rate, mod_rate)
        scores[f"{mod_rate:.0f}"] = round(score, 4)
    passed = max(
        (float(rate) for rate, score in scores.items() if score >= settings.mtf_pass_threshold),
        default=None,
    )
    return scores, passed


def estimate_latency(reference: Iterable[float], recordings: Iterable[Iterable[float]], sample_rate: int) -> tuple[float, float]:
    """Return mean latency and jitter (SD) in milliseconds."""

    ref = _to_array(reference)
    ref -= np.mean(ref)
    latencies: list[float] = []
    for recording in recordings:
        rec = _to_array(recording)
        rec -= np.mean(rec)
        corr = correlate(rec, ref, mode="full")
        lag = int(np.argmax(corr) - (len(ref) - 1))
        latencies.append(1000.0 * lag / sample_rate)
    mean_latency = float(np.mean(latencies)) if latencies else 0.0
    jitter = float(np.std(latencies, ddof=1)) if len(latencies) > 1 else 0.0
    return mean_latency, jitter


__all__ = ["compute_mtf", "estimate_latency"]
