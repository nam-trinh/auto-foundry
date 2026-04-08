import { Search } from "lucide-react";
import type { WorkbenchFilters } from "@/app/App";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { SourceType, WorkbenchData } from "@/types/domain";

interface TopbarProps {
  data: WorkbenchData;
  filters: WorkbenchFilters;
  setFilters: React.Dispatch<React.SetStateAction<WorkbenchFilters>>;
}

export function Topbar({ data, filters, setFilters }: TopbarProps) {
  const sourceTypes = Array.from(new Set(data.sources.map((source) => source.type)));

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/85 px-5 py-4 backdrop-blur-xl">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-muted-foreground">Signal intelligence</p>
          <h2 className="mt-1 text-xl font-semibold">Opportunity discovery console</h2>
        </div>
        <div className="grid gap-2 md:grid-cols-[minmax(220px,360px)_150px_150px_120px]">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Search pains, tags, sources..."
              value={filters.search}
              onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))}
            />
          </div>
          <Select
            value={filters.source}
            onChange={(event) => setFilters((current) => ({ ...current, source: event.target.value as "all" | SourceType }))}
          >
            <option value="all">All sources</option>
            {sourceTypes.map((source) => (
              <option key={source} value={source}>
                {source.replace("_", " ")}
              </option>
            ))}
          </Select>
          <Select
            value={filters.severity}
            onChange={(event) => setFilters((current) => ({ ...current, severity: event.target.value as WorkbenchFilters["severity"] }))}
          >
            <option value="all">All severity</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </Select>
          <Select
            value={filters.window}
            onChange={(event) => setFilters((current) => ({ ...current, window: event.target.value as WorkbenchFilters["window"] }))}
          >
            <option value="7d">7 days</option>
            <option value="30d">30 days</option>
            <option value="90d">90 days</option>
          </Select>
        </div>
      </div>
    </header>
  );
}
