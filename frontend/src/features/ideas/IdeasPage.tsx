import { useWorkbench } from "@/app/useWorkbench";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TraceChain } from "@/components/ui/trace-chain";

export function IdeasPage() {
  const { data } = useWorkbench();

  return (
    <div className="grid gap-5 xl:grid-cols-2">
      {data.ideas.map((idea) => {
        const opportunity = data.opportunities.find((item) => item.id === idea.opportunityId);
        const cluster = data.clusters.find((item) => opportunity?.clusterIds.includes(item.id));
        return (
          <Card key={idea.id} className="border-purple-400/30 bg-purple-500/5">
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <Badge tone="purple">Generated startup idea</Badge>
                  <CardTitle className="mt-3 text-xl">{idea.name}</CardTitle>
                </div>
                <Badge tone="amber">Not evidence by itself</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <p className="text-lg leading-7">{idea.pitch}</p>
              <TraceChain items={[idea.name, opportunity?.title ?? "Opportunity", cluster?.title ?? "Cluster", "Complaints", "Sources"]} />
              <div className="grid gap-3 md:grid-cols-2">
                <Info label="Target user" value={idea.targetUser} />
                <Info label="Problem solved" value={idea.problemSolved} />
                <Info label="MVP" value={idea.mvp} />
                <Info label="Generated at" value={new Date(idea.generatedAt).toLocaleString()} />
              </div>
              <section>
                <h3 className="font-semibold">Monetization hypotheses</h3>
                <div className="mt-2 flex flex-wrap gap-2">{idea.monetization.map((item) => <Badge key={item} tone="green">{item}</Badge>)}</div>
              </section>
              <section>
                <h3 className="font-semibold">Risks</h3>
                <div className="mt-2 space-y-2">{idea.risks.map((risk) => <p key={risk} className="rounded-xl bg-background/70 p-3 text-sm text-muted-foreground">{risk}</p>)}</div>
              </section>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-background/70 p-3">
      <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-sm">{value}</p>
    </div>
  );
}
