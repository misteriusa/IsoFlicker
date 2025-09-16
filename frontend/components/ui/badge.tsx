import * as React from "react";
import { cn } from "../../lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: "safe" | "warn" | "info";
}

const toneClasses: Record<NonNullable<BadgeProps["tone"]>, string> = {
  safe: "bg-emerald-500/10 text-emerald-300 border border-emerald-500/40",
  warn: "bg-amber-500/10 text-amber-200 border border-amber-500/40",
  info: "bg-sky-500/10 text-sky-200 border border-sky-500/40",
};

export function Badge({ className, tone = "info", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium uppercase tracking-wide",
        toneClasses[tone],
        className
      )}
      {...props}
    />
  );
}
