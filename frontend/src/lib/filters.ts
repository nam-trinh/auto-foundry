import type { Complaint, SourceType, WorkbenchData } from "@/types/domain";
import type { WorkbenchFilters } from "@/app/App";

export function filterComplaints(complaints: Complaint[], filters: WorkbenchFilters) {
  const query = filters.search.trim().toLowerCase();
  return complaints.filter((complaint) => {
    const matchesQuery =
      !query ||
      [
        complaint.extractedPain,
        complaint.originalText,
        complaint.sourceTitle,
        complaint.tags.join(" "),
        complaint.author,
      ]
        .join(" ")
        .toLowerCase()
        .includes(query);
    const matchesSource = filters.source === "all" || complaint.sourceType === filters.source;
    const matchesSeverity = filters.severity === "all" || complaint.severity === filters.severity;
    return matchesQuery && matchesSource && matchesSeverity;
  });
}

export function sourceName(data: WorkbenchData, sourceId: string) {
  return data.sources.find((source) => source.id === sourceId)?.name ?? sourceId;
}

export function sourceTone(source: SourceType) {
  if (source === "reddit") return "orange";
  if (source === "hacker_news") return "amber";
  if (source === "github_issues") return "purple";
  if (source === "stack_exchange") return "blue";
  return "default";
}
