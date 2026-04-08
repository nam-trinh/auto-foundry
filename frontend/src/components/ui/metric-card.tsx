import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: string | number;
  detail: string;
  accent?: "blue" | "green" | "amber" | "red";
}

export function MetricCard({ label, value, detail, accent = "blue" }: MetricCardProps) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="relative">
        <div
          className={cn(
            "absolute right-4 top-4 h-16 w-16 rounded-full blur-2xl",
            accent === "blue" && "bg-blue-500/30",
            accent === "green" && "bg-emerald-500/30",
            accent === "amber" && "bg-amber-500/30",
            accent === "red" && "bg-red-500/30",
          )}
        />
        <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">{label}</p>
        <p className="mt-3 text-3xl font-semibold">{value}</p>
        <p className="mt-2 text-sm text-muted-foreground">{detail}</p>
      </CardContent>
    </Card>
  );
}
