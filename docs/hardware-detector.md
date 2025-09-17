# Hardware Detector Overview

This module measures whether a playback chain preserves amplitude modulation up to 90 Hz and reports audio latency for phase
alignment. The workflow mirrors the three-stage process defined in the PRD:

1. **Stage A — Digital probe**
   - Enumerate endpoints with MMDevice / `IAudioClient` to capture form factor, mix format, and device period.
   - Run optional loopback capture to confirm the app delivers clean modulation prior to any Bluetooth codec.
2. **Stage B — Acoustic MTF**
   - Play a battery of AM test tones while the user records with a microphone.
   - Use Hilbert demodulation + FFT to compute normalized modulation depth per rate. Scores ≥0.6 pass; <0.4 triggers warnings.
3. **Stage C — Latency & jitter**
   - Emit a click/burst stimulus, record the response N times, and compute latency via cross-correlation with QPC timestamps.

The FastAPI endpoints expose:

- `POST /hardware/analyze/mtf` → returns modulation transfer values.
- `POST /hardware/analyze/latency` → reports mean latency and jitter.
- `POST /hardware/profiles` → stores results keyed by device GUID.
- `GET /hardware/profiles` → returns stored profiles for display in the frontend.

All computations are designed to be reproducible offline. See `backend/app/services/hardware_analysis.py` for the Hilbert/FFT
implementation and `frontend/app/hardware/page.tsx` for the UI presentation.
