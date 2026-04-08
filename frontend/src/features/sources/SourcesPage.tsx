import { useWorkbench } from "@/app/useWorkbench";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function SourcesPage() {
  const { data } = useWorkbench();

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {data.sources.map((source) => (
        <Card key={source.id}>
          <CardHeader>
            <div className="flex items-start justify-between gap-4">
              <div>
                <CardTitle>{source.name}</CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">{source.type} · {source.query}</p>
              </div>
              <Badge tone={source.health === "healthy" ? "green" : source.health === "degraded" ? "amber" : "red"}>{source.health}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div className="rounded-xl bg-muted p-3"><p className="text-muted-foreground">Discovered</p><p className="text-xl font-semibold">{source.discoveredCount}</p></div>
              <div className="rounded-xl bg-muted p-3"><p className="text-muted-foreground">Freshness</p><p className="text-xl font-semibold">{source.freshnessHours}h</p></div>
              <div className="rounded-xl bg-muted p-3"><p className="text-muted-foreground">Last run</p><p className="text-xs">{new Date(source.lastIngestedAt).toLocaleString()}</p></div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
