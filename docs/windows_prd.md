# Windows 11 IsoFlicker PRD Snapshot

This document captures the essential requirements provided for the Windows-only IsoFlicker build. Use it as the contract between the native engine and the control plane.

## Rendering & Timing

- Direct3D 11 flip-model swap chain with waitable frame latency handle.
- QueryPerformanceCounter timestamps to compute effective Hz and jitter percentiles.
- Phase accumulator to align flicker frequency to monitor refresh; show “Exact/Approx” badge.
- Helper UX to guide users toward 120 Hz refresh and VRR/DRR overrides.

## Audio

- WASAPI (exclusive preferred) at 48/96 kHz with float buffers.
- Raised-cosine edges on all amplitude transitions to avoid spectral splatter.
- Support nested envelopes (theta→gamma), stochastic noise toggles, and slow burst presets.

## Safety & Guardrails

- WCAG 2.3.1 compliance outside the session canvas.
- Consent gate with epilepsy/hyper-sensitivity warnings.
- WHO/NIOSH-derived SPL ranges with Low/Med/High indicator.
- Auto blank on focus loss or display refresh change.

## Telemetry & Export

- Per-frame logging: QPC timestamp, frame index, visual state, target Hz, detected refresh.
- Summary metrics: effective Hz, jitter percentiles, dropped frames.
- Export CSV/JSON with preset metadata and safety flags.

## Default Presets

Reference `data/presets/default_presets.json` for the shipped catalog. Categories:

- **Category A – Proven (physiology-grade)**: Gamma 40, ASSR 90, Alpha 10 visual.
- **Category B – Experimental**: Theta→Gamma nesting, A/V 40 phase study, Alpha pre-task, Slow 0.8 open-loop, Stochastic resonance assist.

Each preset card surfaces the expected effect, rationale, and safety callouts.
