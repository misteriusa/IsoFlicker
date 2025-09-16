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
        <p className="text-sm leading-relaxed">{preset.expected}</p>
        <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-3 text-xs text-slate-400">
          <p className="font-semibold uppercase tracking-wide text-slate-300">Science</p>
          <p className="mt-1 whitespace-pre-line">{preset.rationale}</p>
        </div>
        <p className="text-xs text-amber-200/80">Safety: {preset.safety_notes}</p>
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Depth: {preset.depth ?? "—"}</span>
          <span>Duration: {preset.duration_minutes ?? "—"} min</span>
          <span>Visual: {preset.visual_enabled ? `${preset.visual_rate_hz} Hz` : "none"}</span>
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
