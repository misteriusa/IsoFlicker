import { ArrowUpRight } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import type { Preset } from "../lib/types";
import { PrecisionBadge } from "./precision-badge";

export interface PresetCardProps {
  preset: Preset;
  onSelect?: (preset: Preset) => void;
}

export function PresetCard({ preset, onSelect }: PresetCardProps) {
  const audio = preset.audio_config as Record<string, unknown>;
  const visual = preset.visual_config as Record<string, unknown>;
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>{preset.label}</CardTitle>
            <p className="text-sm text-slate-400">Category {preset.category}</p>
          </div>
          <PrecisionBadge preset={preset} />
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-slate-200">
        <p className="text-sm leading-relaxed">{preset.expected_effects}</p>
        <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-3 text-xs text-slate-400">
          <p className="font-semibold uppercase tracking-wide text-slate-300">Science</p>
          <p className="mt-1 whitespace-pre-line">{preset.rationale}</p>
          {preset.mechanism && (
            <p className="mt-2 whitespace-pre-line text-slate-300">Mechanism: {preset.mechanism}</p>
          )}
        </div>
        <p className="text-xs text-amber-200/80">
          {preset.safety_label ? `${preset.safety_label} · ` : null}
          Safety: {preset.safety_notes}
        </p>
        <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 md:grid-cols-3">
          <span>
            Audio rate: {(audio.mod_rate_hz as number | undefined) ?? (audio.chirp_start_hz as number | undefined) ?? preset.mod_rate_hz ?? "—"} Hz
          </span>
          <span>Depth: {preset.depth ?? (audio.depth as number | undefined) ?? (audio.depth_each as number | undefined) ?? "—"}</span>
          <span>Duration: {preset.duration_minutes ?? "—"} min</span>
          <span>
            Visual: {preset.visual_enabled ? `${preset.visual_rate_hz ?? (visual.rate_hz as number | string | undefined) ?? "?"} Hz` : "none"}
          </span>
          <span>Carrier: {(preset.carrier_type ?? (audio.carrier as string | undefined) ?? "—") as string}</span>
          <span>Photosensitive: {preset.photosensitivity_flag ? "Yes" : "No"}</span>
        </div>
        <Button
          variant="outline"
          className="w-full"
          onClick={() => onSelect?.(preset)}
        >
          Queue preset
          <ArrowUpRight className="ml-2 h-4 w-4" aria-hidden="true" />
        </Button>
      </CardContent>
    </Card>
  );
}
