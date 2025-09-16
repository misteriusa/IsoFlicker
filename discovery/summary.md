# Discovery Summary — IsoFlicker Windows Stack

This document captures the five-phase kickoff loop (Recon → Curation → Vendoring → Bootstrap → Pull Request) for the dedicated Windows 11 build. Scores use a 1–5 scale (5 = excellent fit).

## 1. Recon

**Primary keywords**: `directx waitable swap chain`, `dxgi flip discard sample`, `wasapi exclusive mode python`, `portaudio amplitude modulation`, `qpc high resolution timing`, `wcag flashing guidance`, `fastapi sqlmodel starter`, `next.js shadcn research dashboard`.

**Harvested assets**

| Asset | Type | Notes |
| --- | --- | --- |
| Microsoft DirectX 11 samples | Code | Official waitable swap chain example (FlipDiscard, frame latency wait). |
| Microsoft WASAPI loopback + exclusive sample | Code | Baseline for sample-accurate buffers and render thread management. |
| SQLModel FastAPI template | Repo | Modern typed ORM baseline; supports SQLite for quick persistence. |
| Next.js + Tailwind + shadcn/ui starter | Repo | Gives accessible UI primitives and dark-mode aware cards/dialogs. |
| WHO Safe Listening Q&A | Article | Provides language for SPL guardrails. |
| Epilepsy Foundation photosensitive seizure review | Article | Provides up-to-date warnings for 3–60 Hz flicker. |

## 2. Curation

| Asset | Relevance | License | Maintenance | Quality | Bus Factor | Security | Fit Score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DirectX 11 waitable swap chain sample | 5 | MIT | 5 | 5 | 4 | 5 | **4.8** |
| WASAPI exclusive mode sample | 5 | MIT | 4 | 4 | 3 | 5 | **4.3** |
| SQLModel template | 4 | MIT | 4 | 5 | 3 | 4 | **4.0** |
| shadcn/ui components | 4 | MIT | 5 | 5 | 3 | 4 | **4.2** |
| miniaudio (for optional noise injection) | 3 | MIT | 5 | 4 | 3 | 4 | **3.8** |
| PortAudio | 3 | MIT | 4 | 4 | 3 | 3 | **3.4** |

## 3. Vendoring Plan

Vendored code will live in `third_party/` with commit hashes pinned in `inventory.yml`. For this iteration we ship metadata only (no large source drops) because Microsoft samples must be built from their official repository.

Planned pickups for next iteration:

- `microsoft/DirectX-Graphics-Samples` — `Samples/Desktop/DX11WaitableSwapChain`
- `microsoft/Windows-classic-samples` — `Samples/Win7Samples/multimedia/audio/render` (WASAPI exclusive)
- `tiangolo/sqlmodel` — schema utilities (already available via PyPI; no vendoring required)
- `shadcn/ui` — generated components (we reference the CLI output and include minimal primitives).

## 4. Bootstrap Summary

The new scaffolding includes:

- **Data**: JSON preset catalog mirroring the PRD categories and research metadata.
- **Backend**: FastAPI + SQLModel service with preset endpoints, log ingestion, and CSV export stub hooks.
- **Frontend**: Next.js (App Router) + Tailwind + shadcn-inspired components for preset browsing and precision badges.
- **Windows Client Skeleton**: D3D11/WASAPI C++ entry point (staged for implementation in `windows/`).
- **DevOps**: Docker Compose stack, CI workflow, dev container, bootstrap + ingest scripts, ADR, and CHANGELOG seed.

## 5. Pull Request Notes

- Conventional commit messages follow `feat:`, `chore:`, and `docs:` prefixes.
- ADR-0001 captures the Windows architecture split (native stim engine + web control plane).
- CI covers Ruff/pytest for Python and Vitest for the UI. Coverage tracking is enabled through pytest-cov and Vitest `--coverage`.
- `REVIEW:` and `TODO:` comments are placed where deeper hardware integration is still needed.

