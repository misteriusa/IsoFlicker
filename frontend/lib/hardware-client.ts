const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${DEFAULT_BASE_URL}${path}`, {
    headers: { "Accept": "application/json", "Content-Type": "application/json" },
    cache: "no-store",
    ...init
  });
  if (!response.ok) {
    throw new Error(`Hardware request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function fetchHardwareProfiles(): Promise<HardwareProfile[]> {
  return request<HardwareProfile[]>("/hardware/profiles");
}

export type HardwareProfile = {
  id: number;
  device_guid: string;
  friendly_name: string;
  form_factor?: string | null;
  mix_format?: string | null;
  mtf_pass_hz?: number | null;
  mtf_scores: Record<string, number>;
  latency_ms?: number | null;
  latency_jitter_ms?: number | null;
  tested_at: string;
  notes?: string | null;
};
