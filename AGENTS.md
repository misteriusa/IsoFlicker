# Repository Guidelines

## Project Structure & Modules
- Root Python app: `starter.py` launches the PyQt5 GUI and calls `integrated_isoflicker.main()`.
- Core processing: `integrated_isoflicker.py` (video pipeline, visual effects, SINE presets, overlays).
- Audio generation: `advanced_isochronic_generator.py` (waveforms, modulation, preset generation).
- Utilities: `file_optimizer.py` (FFmpeg compression), `preset_converter.py` (XML ⇄ .sin), `text_overlay.py` (overlay UI).
- Editors: `sine_editor_with_xml.py`, `sine_editor.py`, `visual_preview.py` (helpers/UI), legacy `isoFlickerGUI.py`.
- Environment/assets: `requirements.txt`, optional `ffmpeg-7.1-full_build/`, `venv/`, `Backup/`, `sine/` (related editor resources).

## Build, Run, and Dev Commands
- Create venv (POSIX): `python3 -m venv .venv && source .venv/bin/activate`
- Create venv (Windows): `python -m venv venv && venv\Scripts\activate`
- Install deps: `pip install -r requirements.txt`
- Launch app: `python starter.py`
- Windows one‑shot: run `startEnhancedIsoFlicker.bat` (sets PATH to bundled FFmpeg when present).

## Coding Style & Naming
- Python, PEP 8, 4‑space indent; keep functions small and pure where feasible.
- Names: modules `snake_case.py`; functions/vars `snake_case`; classes `PascalCase`.
- Imports: prefer explicit module imports; avoid wildcards.
- Optional formatting: if available, run `black .` (line length 88) and `ruff .` before PRs.

## Testing Guidelines
- No formal test suite yet. Add focused unit tests for pure logic (e.g., envelope math in `advanced_isochronic_generator.py`) using `pytest` when contributing.
- Smoke test UI: launch `python starter.py`, process a short sample clip (5–10s), verify audio tone, visual flicker, overlays, and exported file size/codec.
- For optimizer changes, validate with `ffprobe` output and compare before/after sizes.

## Commit & Pull Requests
- Commits: imperative, concise subjects (e.g., "Add trapezoid modulation envelope"). Group by module.
- PRs must include: purpose, summary of changes, steps to reproduce, sample command, and screenshots/GIFs for UI changes.
- Link related issues; note OS, Python, and FFmpeg versions when reporting processing bugs.

## Security & Configuration
- FFmpeg required for video I/O. On Windows, the `.bat` script will use `ffmpeg-7.1-full_build/bin` if PATH lacks FFmpeg. Otherwise install from ffmpeg.org and ensure it’s on PATH.
- Do not commit large media exports; share test clips via external links.
- Keep platform specifics in `.bat`/launcher scripts; avoid hardcoded absolute paths.

