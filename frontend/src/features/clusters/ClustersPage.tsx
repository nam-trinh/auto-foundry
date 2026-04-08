import { useState } from "react";
import { useWorkbench } from "@/app/useWorkbench";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Drawer } from "@/components/ui/drawer";
import { TraceChain } from "@/components/ui/trace-chain";
import type { ProblemCluster } from "@/types/domain";

export function ClustersPage() {
  const { data } = useWorkbench();
  const [selected, setSelected] = useState<ProblemCluster | null>(null);

  return (
    <div className="space-y-5">
      <div className="grid gap-4 lg:grid-cols-2">
        {data.clusters.map((cluster) => (
          <Card key={cluster.id} className="cursor-pointer transition hover:border-primary/50" onClick={() => setSelected(cluster)}>
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <CardTitle>{cluster.title}</CardTitle>
                <Badge tone={cluster.trend === "rising" ? "red" : cluster.trend === "stable" ? "amber" : "green"}>{cluster.trend} {cluster.trendDelta}%</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{cluster.summary}</p>
              <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
                <div className="rounded-xl bg-muted p-3"><p className="text-muted-foreground">Count</p><p className="text-lg font-semibold">{cluster.count}</p></div>
                <div className="rounded-xl bg-muted p-3"><p className="text-muted-foreground">Severity</p><p className="text-lg font-semibold">{cluster.averageSeverity}</p></div>
                <div className="rounded-xl bg-muted p-3"><p className="text-muted-foreground">Sources</p><p className="text-lg font-semibold">{cluster.sourceDistribution.length}</p></div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">{cluster.tags.map((tag) => <Badge key={tag}>{tag}</Badge>)}</div>
            </CardContent>
          </Card>
        ))}
      </div>
      <Drawer open={Boolean(selected)} title={selected?.title ?? ""} subtitle={selected?.summary} onClose={() => setSelected(null)}>
        {selected && (
          <div className="space-y-5">
            <TraceChain items={["Problem Cluster", `${selected.count} complaints`, `${selected.opportunityIds.length} opportunities`]} />
            <section>
              <h3 className="font-semibold">Representative quotes</h3>
              <div className="mt-3 space-y-3">
                {selected.representativeQuotes.map((quote) => <blockquote key={quote} className="rounded-xl border border-border bg-background/70 p-3 text-sm">“{quote}”</blockquote>)}
              </div>
            </section>
            <section>
              <h3 className="font-semibold">Source distribution</h3>
              <div className="mt-3 grid gap-2">
                {selected.sourceDistribution.map((item) => <div key={item.source} className="flex justify-between rounded-xl bg-muted p-3 text-sm"><span>{item.source}</span><span>{item.count}</span></div>)}
              </div>
            </section>
            <section>
              <h3 className="font-semibold">Linked complaints</h3>
              <div className="mt-3 space-y-2">
                {selected.complaintIds.map((id) => {
                  const complaint = data.complaints.find((item) => item.id === id);
                  return complaint ? <p key={id} className="rounded-xl bg-muted p-3 text-sm">{complaint.extractedPain}</p> : null;
                })}
              </div>
            </section>
          </div>
        )}
      </Drawer>
    </div>
  );
}
