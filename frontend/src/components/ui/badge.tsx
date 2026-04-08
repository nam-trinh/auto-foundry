import * as React from "react";
import { cn } from "@/lib/utils";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  tone?: "default" | "blue" | "green" | "amber" | "red" | "purple";
};

export function Badge({ className, tone = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
        tone === "default" && "border-border bg-muted text-muted-foreground",
        tone === "blue" && "border-blue-400/30 bg-blue-500/10 text-blue-200",
        tone === "green" && "border-emerald-400/30 bg-emerald-500/10 text-emerald-200",
        tone === "amber" && "border-amber-400/30 bg-amber-500/10 text-amber-200",
        tone === "red" && "border-red-400/30 bg-red-500/10 text-red-200",
        tone === "purple" && "border-purple-400/30 bg-purple-500/10 text-purple-200",
        className,
      )}
      {...props}
    />
  );
}
