# Discovery Summary — IsoFlicker Windows Stack

This document captures the six-phase kickoff loop (Recon → Curation → Vendoring → Bootstrap → Validation → Pull Request) for the
research-heavy Windows build. Scores follow the 0–100 Fit Score formula: `30×Relevance + 15×License + 15×Maintenance + 15×Quality + 10×BusFactor + 10×Security + 5×Docs` (each component ∈ [0,1]).

## 1. Recon

**Keyword expansion**: `auditory steady-state toolkit`, `hilbert envelope fft`, `amplitude modulation transfer`, `fastapi sqlmodel alembic postgres`, `psycopg async`, `nextjs shadcn research dashboard`, `ruff mypy github actions matrix`, `bluetooth codec mtf analyzer`.

### Backend & Data (Top 8)
1. **FastAPI** — Modern ASGI framework with typed routing and dependency injection.
2. **SQLModel** — SQLAlchemy + Pydantic hybrid for typed ORM models.
3. **Alembic** — Schema migration tool paired with SQLAlchemy metadata.
4. **psycopg (binary)** — PostgreSQL driver with asyncio hooks and binary wheels.
5. **Pydantic Settings** — Env-driven configuration management.
6. **Uvicorn** — ASGI server with hot-reload and HTTP/2 support.
7. **Redis OM** — Optional caching layer for session metrics (evaluated, not yet adopted).
8. **Celery** — Background task framework (considered for future telemetry export batches).

### Signal Processing & Audio Tooling (Top 8)
1. **NumPy** — Core numerical operations, FFT, vectorized math.
2. **SciPy.signal** — Hilbert transform, correlation, and windowing utilities.
3. **Soundfile** — Read/write WAV/FLAC with float precision (candidate for future capture pipeline).
4. **librosa** — Feature extraction and time-frequency analysis (reference implementation for envelope MT).
5. **pyFFTW** — Accelerated FFT using FFTW (optional performance boost).
6. **aubio** — Onset/pitch detection; evaluated for latency click detection alternatives.
7. **miniaudio** — Lightweight audio I/O (considered for cross-platform prototypes).
8. **PyAudio** — Legacy PortAudio bindings (kept as fallback reference).

### Frontend & UI (Top 8)
1. **Next.js App Router** — React meta-framework with server components.
2. **Tailwind CSS** — Utility-first styling with dark-mode tokens.
3. **shadcn/ui** — Headless Radix primitives with opinionated styling.
4. **Radix UI** — Accessible interactive components underpinning shadcn.
5. **Lucide Icons** — Open-source icon set used across cards and buttons.
6. **Recharts** — Candidate for future MTF charting.
7. **TanStack Query** — Data-fetch caching (future optimization for profile fetches).
8. **nivo** — Alternative charting library with SSR support.

### Quality, Tooling & CI (Top 8)
1. **Ruff** — Python linting + formatting with blazing speed.
2. **mypy** — Static type checker for backend modules.
3. **pytest** — Backend test runner with coverage support.
4. **Vitest** — Frontend unit testing with Vite compatibility.
5. **Prettier** — Formatting for TypeScript/JSON/MD.
6. **GitHub Actions** — CI runner with matrix support.
7. **Playwright** — Candidate for future end-to-end tests.
8. **Dependabot** — Automated dependency updates (to be enabled later).

## 2. Curation (Top-3 per category, Fit Score ≥ 70)

| Category | Asset | Fit Score | Notes |
| --- | --- | --- | --- |
| Backend & Data | FastAPI | 94 | MIT, active releases, strong docs, broad community.
| Backend & Data | SQLModel | 92 | MIT, typed models, maintained by Tiangolo, aligns with SQLAlchemy ecosystem.
| Backend & Data | Alembic | 90 | Core SQLAlchemy migration tool, MIT, mature.
| Signal Processing | NumPy | 95 | BSD, massive community, required for DSP.
| Signal Processing | SciPy | 92 | BSD, rich signal-processing suite.
| Signal Processing | Soundfile | 74 | BSD, maintained; optional for future capture routines.
| Frontend & UI | Next.js | 96 | MIT, Vercel-backed, matches SSR needs.
| Frontend & UI | Tailwind CSS | 93 | MIT, strong docs/community.
| Frontend & UI | shadcn/ui | 90 | MIT, composable primitives, regularly updated.
| Quality & CI | Ruff | 93 | MIT, consolidated lint/format.
| Quality & CI | mypy | 88 | MIT, typed enforcement, active maintenance.
| Quality & CI | Vitest | 86 | MIT, fast TS testing with good docs.

## 3. Vendoring Plan

- `fastapi`, `sqlmodel`, `alembic`, `psycopg`, `numpy`, `scipy`, `soundfile`, `next`, `tailwindcss`, `shadcn/ui`, `ruff`, `mypy`, and `vitest` pinned in `third_party/inventory.yml` with LICENSE copies in `third_party/LICENSES/`.
- Microsoft platform samples (DirectX waitable swap chain, WASAPI exclusive) tracked by metadata only; source stays external per license guidance.
- Quarterly review cadence captured in `third_party/README.md`.

## 4. Bootstrap Summary

- **Data**: JSON catalog refreshed to `2024.07-experimental` with categories A/B/E and 15 new experimental presets referencing literature.
- **Backend**: FastAPI + SQLModel service with Alembic migrations, Postgres-ready config, hardware detector analytics (Hilbert/FFT + latency), and session logging.
- **Frontend**: Next.js App Router UI with updated preset cards, hardware detector dashboard, and safety documentation routes.
- **Tooling**: Docker Compose with Postgres, GitHub Actions matrix (Python 3.11/3.12 + Node 20), Ruff + mypy enforcement, Prettier/mypy hooks, and bootstrap script triggering migrations.

## 5. Validation Snapshot

- `pytest` covers presets, logs, and hardware detector APIs using synthetic AM/latency fixtures.
- `vitest` validates preset card rendering with expanded schema.
- `ruff`, `mypy`, and `prettier --check` enforced via CI and pre-commit.
- Alembic migration `20240705_01_initial` reproducibly materializes all SQLModel tables.

## 6. Pull Request Notes

- Conventional commits (`feat`, `chore`, `docs`, `test`) recorded for backend, frontend, infra, and docs changes.
- ADR-0001 updated to reflect hardware analytics and strengthened CI guardrails.
- CHANGELOG bumped to `0.2.0` summarizing experimental presets, detector API, and tooling upgrades.
- Outstanding `REVIEW:` markers reserved for Windows-native capture implementation (not yet merged into this PR).
