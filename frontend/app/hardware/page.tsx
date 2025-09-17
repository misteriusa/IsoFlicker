import { Suspense } from "react";
import { fetchHardwareProfiles } from "../../lib/hardware-client";
import type { HardwareProfile } from "../../lib/hardware-client";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";

async function HardwareProfiles() {
  const profiles: HardwareProfile[] = await fetchHardwareProfiles();
  if (profiles.length === 0) {
    return <p className="text-sm text-slate-400">No measurements stored yet. Run the detector to populate results.</p>;
  }
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {profiles.map((profile) => {
        const mtfSummary = Object.entries(profile.mtf_scores)
          .map(([rate, score]) => `${rate} Hz: ${(score * 100).toFixed(0)}%`)
          .join(" · ");
        return (
          <Card key={profile.id} className="bg-slate-900/70">
            <CardHeader>
              <CardTitle className="text-lg text-slate-100">{profile.friendly_name}</CardTitle>
              <p className="text-xs text-slate-400">GUID: {profile.device_guid}</p>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-slate-200">
              <p>Form factor: {profile.form_factor ?? "Unknown"}</p>
              <p>Mix format: {profile.mix_format ?? "Unknown"}</p>
              <p>AM fidelity ≥{profile.mtf_pass_hz ?? "?"} Hz · {mtfSummary}</p>
              <p>
                Latency: {profile.latency_ms?.toFixed(1) ?? "?"} ms ± {profile.latency_jitter_ms?.toFixed(1) ?? "?"} ms
              </p>
              <p>Tested at: {new Date(profile.tested_at).toLocaleString()}</p>
              {profile.notes && <p className="text-xs text-slate-400">Notes: {profile.notes}</p>}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

export default function HardwarePage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-6 px-6 py-10">
      <header className="space-y-3">
        <h1 className="text-3xl font-bold text-slate-100">Hardware Detector</h1>
        <p className="text-sm text-slate-300">
          Validate whether headphones or speakers preserve amplitude modulation and measure audio latency for sync. Results are
          stored locally for each device GUID so you can compare Bluetooth codecs, USB DACs, and wired outputs.
        </p>
      </header>
      <Suspense fallback={<p className="text-slate-400">Loading hardware profiles…</p>}>
        {/* @ts-expect-error Server Component async boundary */}
        <HardwareProfiles />
      </Suspense>
    </main>
  );
}
