import { Preset, Category } from "./types";

const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${DEFAULT_BASE_URL}${path}`, {
    headers: { "Accept": "application/json" },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`Backend request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function fetchPresets(): Promise<Preset[]> {
  return request<Preset[]>("/presets/");
}

export async function fetchCategories(): Promise<Category[]> {
  return request<Category[]>("/presets/categories");
}
