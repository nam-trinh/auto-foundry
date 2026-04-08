import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useWorkbench } from "@/app/useWorkbench";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { Badge } from "@/components/ui/badge";
import { ScoreBreakdown } from "@/components/ui/score-breakdown";
import { trendSeries } from "@/data/mockData";
import { filterComplaints } from "@/lib/filters";

export function OverviewPage() {
  const { data, filters } = useWorkbench();
  const complaints = filterComplaints(data.complaints, filters);
  const topOpportunities = data.opportunities.slice(0, 3);
  const risingPain = [...data.clusters].sort((a, b) => b.trendDelta - a.trendDelta).slice(0, 4);
  const sourceMix = data.sources.map((source) => ({ name: source.name, count: source.discoveredCount }));

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Complaints" value={complaints.length} detail="Filtered extracted pains" accent="blue" />
        <MetricCard label="Clusters" value={data.clusters.length} detail="Recurring problem groups" accent="green" />
        <MetricCard label="Opportunities" value={data.opportunities.length} detail="Ranked market openings" accent="amber" />
        <MetricCard label="Pipeline runs" value={data.runs.length} detail="Recent ingestion jobs" accent="red" />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Complaint and opportunity trend</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
                <XAxis dataKey="day" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 12 }} />
                <Area type="monotone" dataKey="complaints" stroke="#60a5fa" fill="#2563eb55" />
                <Area type="monotone" dataKey="opportunities" stroke="#34d399" fill="#05966955" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Source mix</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sourceMix} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
                <XAxis type="number" stroke="#94a3b8" />
                <YAxis type="category" dataKey="name" stroke="#94a3b8" width={120} />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 12 }} />
                <Bar dataKey="count" fill="#60a5fa" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Top opportunities</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {topOpportunities.map((opportunity) => (
              <div key={opportunity.id} className="rounded-2xl border border-border bg-background/60 p-4">
                <div className="mb-3 flex items-start justify-between gap-4">
                  <div>
                    <Badge tone="blue">Rank #{opportunity.rank}</Badge>
                    <h3 className="mt-2 text-lg font-semibold">{opportunity.title}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{opportunity.summary}</p>
                  </div>
                  <Badge tone={opportunity.confidence === "evidence-backed" ? "green" : "amber"}>{opportunity.confidence}</Badge>
                </div>
                <ScoreBreakdown score={opportunity.score} />
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Fastest-rising pain points</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {risingPain.map((cluster) => (
              <div key={cluster.id} className="rounded-xl border border-border bg-background/60 p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium">{cluster.title}</p>
                  <Badge tone={cluster.trendDelta > 20 ? "red" : "amber"}>+{cluster.trendDelta}%</Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{cluster.summary}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
