import { ColumnDef } from "@tanstack/react-table";
import { useMemo } from "react";
import { useWorkbench } from "@/app/useWorkbench";
import { DataTable } from "@/components/tables/DataTable";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { PipelineRun } from "@/types/domain";

export function RunsPage() {
  const { data, filters } = useWorkbench();
  const columns = useMemo<ColumnDef<PipelineRun>[]>(
    () => [
      { accessorKey: "id", header: "Run" },
      { accessorKey: "sourceName", header: "Source" },
      { accessorKey: "jobType", header: "Job type", cell: ({ row }) => <Badge tone="blue">{row.original.jobType}</Badge> },
      { accessorKey: "status", header: "Status", cell: ({ row }) => <Badge tone={row.original.status === "success" ? "green" : row.original.status === "failed" ? "red" : "amber"}>{row.original.status}</Badge> },
      { accessorKey: "fetched", header: "Fetched" },
      { accessorKey: "inserted", header: "Inserted" },
      { accessorKey: "updated", header: "Updated" },
      { accessorKey: "skipped", header: "Skipped" },
      { accessorKey: "error", header: "Error", cell: ({ row }) => <span className="text-red-200">{row.original.error ?? "—"}</span> },
    ],
    [],
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pipeline run history</CardTitle>
      </CardHeader>
      <CardContent>
        <DataTable data={data.runs} columns={columns} globalFilter={filters.search} />
      </CardContent>
    </Card>
  );
}
