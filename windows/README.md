# IsoFlicker Windows Native Prototype

This folder contains the Windows-only native stimulation engine described in the PRD. The CMake project builds a small prototype that exercises:

- DXGI waitable swap chain with flip-discard to guarantee vsync pacing.
- WASAPI audio client configured for floating-point output and modulation placeholder.
- QueryPerformanceCounter-based telemetry logging exported as CSV.

## Building

```powershell
cmake -S . -B build -G "Visual Studio 17 2022"
cmake --build build --config Release
```

Run the resulting executable from the repo root to create `telemetry.csv` alongside the binary. The application currently flips a blank swap chain and renders a sinusoidal AM tone—see `REVIEW` comments for remaining work (contrast shaping, raised-cosine envelope, and precision badges in-window).
