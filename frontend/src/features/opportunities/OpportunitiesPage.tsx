import { useState } from "react";
import { useWorkbench } from "@/app/useWorkbench";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Drawer } from "@/components/ui/drawer";
import { ScoreBreakdown } from "@/components/ui/score-breakdown";
import { TraceChain } from "@/components/ui/trace-chain";
import type { Opportunity } from "@/types/domain";

export function OpportunitiesPage() {
  const { data } = useWorkbench();
  const [selected, setSelected] = useState<Opportunity | null>(null);

  return (
    <div className="space-y-4">
      {data.opportunities.map((opportunity) => (
        <Card key={opportunity.id} className="cursor-pointer transition hover:border-primary/50" onClick={() => setSelected(opportunity)}>
          <CardContent className="grid gap-5 lg:grid-cols-[90px_1fr_360px]">
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">Rank</p>
              <p className="mt-2 text-4xl font-semibold">#{opportunity.rank}</p>
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="green">{opportunity.confidence}</Badge>
                <Badge tone={opportunity.trend === "rising" ? "red" : "amber"}>{opportunity.trend}</Badge>
              </div>
              <h3 className="mt-3 text-xl font-semibold">{opportunity.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{opportunity.summary}</p>
              <p className="mt-3 text-sm text-blue-200">{opportunity.market}</p>
            </div>
            <ScoreBreakdown score={opportunity.score} />
          </CardContent>
        </Card>
      ))}
      <Drawer open={Boolean(selected)} title={selected?.title ?? ""} subtitle={selected?.summary} onClose={() => setSelected(null)}>
        {selected && (
          <div className="space-y-6">
            <TraceChain items={["Opportunity", `${selected.clusterIds.length} clusters`, `${selected.complaintIds.length} complaints`, "Original sources"]} />
            <ScoreBreakdown score={selected.score} />
            <section>
              <h3 className="font-semibold">Linked clusters</h3>
              <div className="mt-3 space-y-2">
                {selected.clusterIds.map((id) => {
                  const cluster = data.clusters.find((item) => item.id === id);
                  return cluster ? <div key={id} className="rounded-xl bg-muted p-3"><p className="font-medium">{cluster.title}</p><p className="text-sm text-muted-foreground">{cluster.summary}</p></div> : null;
                })}
              </div>
            </section>
            <section>
              <h3 className="font-semibold">Evidence complaints</h3>
              <div className="mt-3 space-y-2">
                {selected.complaintIds.map((id) => {
                  const complaint = data.complaints.find((item) => item.id === id);
                  return complaint ? <blockquote key={id} className="rounded-xl border border-border bg-background/70 p-3 text-sm">“{complaint.originalText}”<br /><a className="mt-2 inline-block text-blue-300" href={complaint.sourceUrl} target="_blank" rel="noreferrer">Source evidence</a></blockquote> : null;
                })}
              </div>
            </section>
            <section>
              <h3 className="font-semibold">Generated ideas</h3>
              <div className="mt-3 space-y-2">
                {data.ideas.filter((idea) => idea.opportunityId === selected.id).map((idea) => <div key={idea.id} className="rounded-xl border border-purple-400/30 bg-purple-500/10 p-3"><Badge tone="purple">Generated concept</Badge><p className="mt-2 font-medium">{idea.name}</p><p className="text-sm text-muted-foreground">{idea.pitch}</p></div>)}
              </div>
            </section>
          </div>
        )}
      </Drawer>
    </div>
  );
}
