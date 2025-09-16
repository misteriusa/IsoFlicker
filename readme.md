# IsoFlicker Pro - Enhanced Features Guide

## Overview

IsoFlicker Pro has been enhanced with a powerful Isochronic Timeline Editor that allows you to create complex entrainment sessions with precise control over frequency transitions, carrier waves, modulation patterns, and more.

## Windows 11 Native Stack (Preview)

The repository now includes a Windows-specific stimulation engine and orchestration layer:

- **`windows/`** — Direct3D 11 + WASAPI prototype with waitable swap chain, QPC telemetry, and CSV export (`cmake -S windows -B build`).
- **`backend/`** — FastAPI + SQLModel service that exposes preset metadata, safety notes, and session logging endpoints.
- **`frontend/`** — Next.js control surface (App Router + Tailwind + shadcn/ui primitives) visualizing Category A/B presets and safety messaging.
- **`scripts/bootstrap.sh`** — One-shot local setup (Python venv + backend install + `npm install`).
- **`scripts/ingest.py`** — Loads `data/presets/default_presets.json` into the SQLModel database.

See `docs/windows_prd.md` for a snapshot of the Windows 11 PRD, and `discovery/summary.md` for the kickoff research trail.

## New Key Features

### Graphical Timeline and Frequency Control
- **Preset Timeline:** Arrange different segments sequentially, each with its own frequency settings
- **Visual Timeline Editor:** See your entire session layout with color-coded segments
- **Precise Frequency Settings:** Set both starting and ending frequencies for smooth transitions

### Advanced Wave Generation Options
- **Carrier Wave Types:** Choose from sine, square, triangle, sawtooth, and noise carriers
- **Modulation Patterns:** Select from classic square wave (on/off), smooth sine wave, trapezoidal, or gaussian modulation

### Intensity and Duration Adjustments
- **Duration Controls:** Set precise duration for each segment
- **Volume/Intensity Control:** Adjust the volume of each segment independently
- **Background Audio:** Mix your isochronic tones with background audio

### Transition Effects and Looping
- **Smooth Transitions:** Create gradual frequency changes with various transition types:
  - Linear (steady change)
  - Exponential (accelerating change)
  - Logarithmic (decelerating change)
  - Quadratic (ease-in/ease-out)
  - Sigmoid (S-curve transition)
- **Looping Options:** Set your entire preset to loop for extended sessions

### Preset Management
- **Save/Load Presets:** Save your carefully designed sessions as ".sin" files
- **Export Audio:** Export your presets as high-quality WAV, FLAC, or MP3 files

## How to Use the Timeline Editor

### Creating a New Preset
1. Switch to the "Timeline Editor" tab
2. Give your preset a name
3. Click "+ Add Segment" to add your first segment
4. Set the desired parameters for each segment:
   - Start Frequency (Hz): The beginning entrainment frequency
   - End Frequency (Hz): The ending entrainment frequency (same as start for constant)
   - Base Frequency (Hz): The carrier wave frequency (typically 100-300 Hz)
   - Duration (sec): Length of the segment in seconds
   - Volume: Intensity of the isochronic tone
   - Transition: Type of frequency change (linear, exponential, etc.)

### Working with Segments
- Click on segments in the timeline to select them
- Add multiple segments to create a complete session
- Arrange segments in sequence to guide brainwave states
- Common progression: Beta → Alpha → Theta → Delta → Theta → Alpha → Beta

### Adding Background Audio
- Click "Select Background" to add ambient sounds or music
- Background audio will loop if shorter than your preset
- Adjust background volume in the settings

### Processing Videos with Timeline Presets
1. In the "Basic Mode" tab, select your input video
2. Return to the "Timeline Editor" tab and design your preset
3. Click "Process Video with Timeline" to apply your preset to the video
4. Configure visual entrainment options in the dialog
5. Choose your output location and format

## Tips for Effective Presets

- **Session Structure:** Start with higher frequencies (Beta: 13-30 Hz), then gradually transition to target frequencies
- **Transitions:** Use smoother transitions (linear or sigmoid) for comfort
- **Duration:** Allow 5-10 minutes for each major brainwave state
- **Audio-Visual Sync:** When processing videos, synchronize audio and visual frequencies for stronger entrainment
- **Testing:** Test your presets before creating long sessions

## Brainwave Frequency Ranges

- **Gamma:** 30-100 Hz (heightened perception, peak concentration)
- **Beta:** 13-30 Hz (active, alert thinking)
- **Alpha:** 8-12 Hz (relaxed awareness, light meditation)
- **Theta:** 4-7 Hz (deep meditation, drowsiness, REM sleep)
- **Delta:** 0.5-4 Hz (deep sleep, healing)

Remember that brainwave entrainment affects different people in different ways. Start with shorter sessions and lower intensities, then adjust based on your experience.
