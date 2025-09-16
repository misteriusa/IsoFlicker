import { Badge } from "./ui/badge";
import type { Preset } from "../lib/types";

export function PrecisionBadge({ preset }: { preset: Preset }) {
  const note = preset.precision_note ?? "Audio only";
  const tone = note.toLowerCase().includes("exact") ? "safe" : note.includes("Audio") ? "info" : "warn";
  return <Badge tone={tone}>{note}</Badge>;
}
