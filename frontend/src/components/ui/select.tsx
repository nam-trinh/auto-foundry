import * as React from "react";
import { cn } from "@/lib/utils";

export function Select({ className, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "h-10 rounded-xl border border-border bg-muted/60 px-3 text-sm outline-none ring-primary/30 transition focus:ring-4",
        className,
      )}
      {...props}
    />
  );
}
