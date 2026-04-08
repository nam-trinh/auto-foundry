import { ColumnDef } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { useWorkbench } from "@/app/useWorkbench";
import { DataTable } from "@/components/tables/DataTable";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TraceChain } from "@/components/ui/trace-chain";
import { filterComplaints, sourceName } from "@/lib/filters";
import type { Complaint } from "@/types/domain";

export function ComplaintsPage() {
  const { data, filters } = useWorkbench();
  const complaints = filterComplaints(data.complaints, filters);
  const [selected, setSelected] = useState<Complaint | undefined>(complaints[0]);
  const columns = useMemo<ColumnDef<Complaint>[]>(
    () => [
      { accessorKey: "extractedPain", header: "Extracted pain" },
      { accessorKey: "severityScore", header: "Severity", cell: ({ row }) => <Badge tone={row.original.severity === "critical" ? "red" : "amber"}>{row.original.severityScore}</Badge> },
      { accessorKey: "sourceType", header: "Source", cell: ({ row }) => <Badge tone="blue">{sourceName(data, row.original.sourceId)}</Badge> },
      { accessorKey: "tags", header: "Tags", cell: ({ row }) => <div className="flex flex-wrap gap-1">{row.original.tags.map((tag) => <Badge key={tag}>{tag}</Badge>)}</div> },
    ],
    [data],
  );
  const cluster = selected ? data.clusters.find((item) => item.id === selected.clusterId) : undefined;
  const opportunity = selected ? data.opportunities.find((item) => item.id === selected.opportunityId) : undefined;

  return (
    <div className="grid gap-5 xl:grid-cols-[1.4fr_0.8fr]">
      <Card>
        <CardHeader>
          <CardTitle>Complaints evidence table</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable data={complaints} columns={columns} globalFilter={filters.search} onRowClick={setSelected} />
        </CardContent>
      </Card>
      <Card className="xl:sticky xl:top-28 xl:self-start">
        <CardHeader>
          <CardTitle>Complaint detail</CardTitle>
        </CardHeader>
        <CardContent>
          {selected ? (
            <div className="space-y-5">
              <TraceChain items={[selected.sourceTitle, cluster?.title ?? "Cluster", opportunity?.title ?? "Opportunity"]} />
              <div>
                <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">Original text</p>
                <blockquote className="mt-2 rounded-xl border border-border bg-background/70 p-4 text-sm leading-6">“{selected.originalText}”</blockquote>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">Extracted pain</p>
                <p className="mt-2 text-lg font-medium">{selected.extractedPain}</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl bg-muted p-3"><p className="text-muted-foreground">Severity</p><p>{selected.severity} ({selected.severityScore})</p></div>
                <div className="rounded-xl bg-muted p-3"><p className="text-muted-foreground">Author</p><p>{selected.author}</p></div>
              </div>
              <a className="text-sm text-blue-300 underline underline-offset-4" href={selected.sourceUrl} target="_blank" rel="noreferrer">Open original source</a>
            </div>
          ) : (
            <p className="text-muted-foreground">Select a complaint to inspect the evidence chain.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
