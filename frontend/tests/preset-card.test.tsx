import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PresetCard } from "../components/preset-card";
import type { Preset } from "../lib/types";

const preset: Preset = {
  id: "gamma40",
  category: "A",
  label: "Gamma 40",
  mod_rate_hz: 40,
  duty_cycle: 0.5,
  depth: 1,
  window_ms: 5,
  carrier_type: "pink-noise",
  carrier_hz: null,
  outer_envelope_rate: null,
  outer_envelope_depth: null,
  phase_options_deg: null,
  duration_minutes: 20,
  visual_enabled: true,
  visual_rate_hz: 40,
  visual_phase_deg: 0,
  precision_note: "Exact at 120 Hz",
  rationale: "Robust ASSR",
  expected: "Strong entrainment",
  safety_notes: "Keep volume comfortable",
  max_volume_pct: 70,
  photosensitivity_flag: true,
  citations: [8, 9]
};

describe("PresetCard", () => {
  it("renders preset details and handles selection", () => {
    const onSelect = vi.fn();
    render(<PresetCard preset={preset} onSelect={onSelect} />);
    expect(screen.getByText(/Gamma 40/i)).toBeInTheDocument();
    expect(screen.getByText(/Strong entrainment/)).toBeVisible();
    const button = screen.getByRole("button", { name: /queue preset/i });
    fireEvent.click(button);
    expect(onSelect).toHaveBeenCalledWith(preset);
  });
});
