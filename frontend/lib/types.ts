export type PresetCategory = "A" | "B";

export interface Preset {
  id: string;
  category: PresetCategory;
  label: string;
  mod_rate_hz?: number | null;
  duty_cycle?: number | null;
  depth?: number | null;
  window_ms?: number | null;
  carrier_type?: string | null;
  carrier_hz?: number | null;
  outer_envelope_rate?: number | null;
  outer_envelope_depth?: number | null;
  phase_options_deg?: number[] | null;
  duration_minutes?: number | null;
  visual_enabled: boolean;
  visual_rate_hz?: number | null;
  visual_phase_deg?: number | null;
  precision_note?: string | null;
  rationale: string;
  expected: string;
  safety_notes: string;
  max_volume_pct?: number | null;
  photosensitivity_flag: boolean;
  citations: number[];
}

export interface Category {
  id: PresetCategory;
  label: string;
  description: string;
}
