# Changelog

## [0.2.0] - 2024-07-05
### Added
- Experimental (research-only) preset catalog entries E-01–E-15 with full rationale, mechanism notes, and citations.
- Hardware detector API (MTF + latency) with SQLModel persistence, Hilbert/FFT analysis helpers, and Alembic migrations.
- Next.js hardware dashboard and safety docs linking to backend results; updated preset UI with mechanism/safety metadata.
- Postgres-ready Docker Compose stack, CI upgrades (Ruff, mypy, pytest, Vitest), and Prettier/mypy pre-commit hooks.
- Discovery recon updates, hardware documentation, and ADR refresh capturing the expanded scope.

## [0.1.0] - 2024-04-04
### Added
- Windows native prototype with D3D11 waitable swap chain and WASAPI scaffold.
- FastAPI + SQLModel backend seeded with research-grade preset catalog and logging endpoints.
- Next.js control panel showcasing presets, safety messaging, and precision badges.
- DevOps scaffolding: Dockerfile, docker-compose, devcontainer, CI workflow, pre-commit config.
- Discovery dossier, ADR-0001, and documentation capturing the Windows PRD and preset rationale.
