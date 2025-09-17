import Link from "next/link";
import { Suspense } from "react";
import { PresetCard } from "../components/preset-card";
import { Button } from "../components/ui/button";
import { fetchCategories, fetchPresets } from "../lib/preset-client";
import type { Preset, Category } from "../lib/types";

async function loadData(): Promise<{ presets: Preset[]; categories: Category[] }> {
  try {
    const [presets, categories] = await Promise.all([fetchPresets(), fetchCategories()]);
    return { presets, categories };
  } catch (error) {
    console.error("Failed to load presets", error);
    return { presets: [], categories: [] };
  }
}

function CategorySection({
  category,
  presets
}: {
  category: Category;
  presets: Preset[];
}) {
  if (presets.length === 0) {
    return null;
  }
  return (
    <section className="space-y-4" aria-labelledby={`category-${category.id}`}>
      <div className="flex items-center justify-between">
        <div>
          <h2 id={`category-${category.id}`} className="text-xl font-semibold text-slate-100">
            {category.label}
          </h2>
          <p className="text-sm text-slate-400">{category.description}</p>
        </div>
        <Button asChild variant="outline">
          <Link href={`/#${category.id}`}>Documentation</Link>
        </Button>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {presets.map((preset) => (
          <PresetCard key={preset.id} preset={preset} />
        ))}
      </div>
    </section>
  );
}

export default async function Page() {
  const { presets, categories } = await loadData();
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-10 px-6 py-10">
      <header className="space-y-4">
        <h1 className="text-3xl font-bold">IsoFlicker Preset Library</h1>
        <p className="max-w-3xl text-sm text-slate-300">
          Explore research-backed presets for the Windows entrainment engine. Each card captures the
          expected physiological response, guardrails, and references outlined in the PRD. Use the
          presets below to orchestrate synchronized visual and auditory sessions.
        </p>
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4 text-xs text-slate-300">
          <p className="font-semibold uppercase tracking-wide text-slate-200">Safety banner</p>
          <p className="mt-1 text-slate-400">
            This app provides sensory stimulation for experimentation and research logging. It does not
            diagnose or treat any condition. Stop immediately if you feel unwell. Keep volume moderate
            and be aware of photosensitivity risks between 3–60 Hz, especially 15–25 Hz high contrast.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="secondary">
            <Link href="/hardware">Open hardware detector results</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/docs/safety">Safety guidance</Link>
          </Button>
        </div>
      </header>
      <Suspense fallback={<p className="text-slate-400">Loading presets…</p>}>
        <div className="space-y-12">
          {categories.map((category) => (
            <CategorySection
              key={category.id}
              category={category}
              presets={presets.filter((preset) => preset.category === category.id)}
            />
          ))}
          {presets.length === 0 && (
            <p className="text-sm text-amber-300">
              Unable to reach the backend. Double-check that the FastAPI service is running on
              <code className="ml-1 rounded bg-slate-800 px-1">http://localhost:8000</code>.
            </p>
          )}
        </div>
      </Suspense>
    </main>
  );
}
