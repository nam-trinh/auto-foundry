import { useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { WorkbenchLayout } from "@/components/layout/WorkbenchLayout";
import { mockData } from "@/data/mockData";
import { ClustersPage } from "@/features/clusters/ClustersPage";
import { ComplaintsPage } from "@/features/complaints/ComplaintsPage";
import { IdeasPage } from "@/features/ideas/IdeasPage";
import { OpportunitiesPage } from "@/features/opportunities/OpportunitiesPage";
import { OverviewPage } from "@/features/overview/OverviewPage";
import { RunsPage } from "@/features/runs/RunsPage";
import { SourcesPage } from "@/features/sources/SourcesPage";
import type { SourceType, WorkbenchData } from "@/types/domain";

export interface WorkbenchFilters {
  search: string;
  source: "all" | SourceType;
  severity: "all" | "low" | "medium" | "high" | "critical";
  window: "7d" | "30d" | "90d";
}

export interface WorkbenchOutletContext {
  data: WorkbenchData;
  filters: WorkbenchFilters;
  setFilters: React.Dispatch<React.SetStateAction<WorkbenchFilters>>;
}

export function App() {
  const [filters, setFilters] = useState<WorkbenchFilters>({
    search: "",
    source: "all",
    severity: "all",
    window: "7d",
  });
  const context = useMemo(() => ({ data: mockData, filters, setFilters }), [filters]);

  return (
    <Routes>
      <Route element={<WorkbenchLayout context={context} />}>
        <Route index element={<OverviewPage />} />
        <Route path="complaints" element={<ComplaintsPage />} />
        <Route path="clusters" element={<ClustersPage />} />
        <Route path="opportunities" element={<OpportunitiesPage />} />
        <Route path="ideas" element={<IdeasPage />} />
        <Route path="sources" element={<SourcesPage />} />
        <Route path="runs" element={<RunsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
