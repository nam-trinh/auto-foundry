export type Severity = "low" | "medium" | "high" | "critical";
export type Trend = "rising" | "stable" | "falling";
export type SourceType = "reddit" | "hacker_news" | "stack_exchange" | "github_issues" | "mock";
export type RunStatus = "success" | "failed" | "running" | "partial";

export interface Source {
  id: string;
  name: string;
  type: SourceType;
  query: string;
  health: "healthy" | "degraded" | "paused";
  lastIngestedAt: string;
  discoveredCount: number;
  freshnessHours: number;
}

export interface Complaint {
  id: string;
  sourceId: string;
  sourceType: SourceType;
  sourceUrl: string;
  sourceTitle: string;
  author: string;
  originalText: string;
  extractedPain: string;
  severity: Severity;
  severityScore: number;
  tags: string[];
  createdAt: string;
  clusterId: string;
  opportunityId: string;
}

export interface ProblemCluster {
  id: string;
  title: string;
  summary: string;
  complaintIds: string[];
  opportunityIds: string[];
  count: number;
  trend: Trend;
  trendDelta: number;
  averageSeverity: number;
  tags: string[];
  representativeQuotes: string[];
  sourceDistribution: Array<{ source: SourceType; count: number }>;
}

export interface ScoreBreakdown {
  frequency: number;
  severity: number;
  willingnessToPay: number;
  urgency: number;
  marketPull: number;
  finalScore: number;
  formula: string;
}

export interface Opportunity {
  id: string;
  rank: number;
  title: string;
  summary: string;
  market: string;
  score: ScoreBreakdown;
  clusterIds: string[];
  complaintIds: string[];
  trend: Trend;
  confidence: "evidence-backed" | "directional" | "thin-evidence";
}

export interface StartupIdea {
  id: string;
  opportunityId: string;
  name: string;
  pitch: string;
  targetUser: string;
  problemSolved: string;
  mvp: string;
  monetization: string[];
  risks: string[];
  generatedAt: string;
  isGenerated: true;
}

export interface PipelineRun {
  id: string;
  sourceId: string;
  sourceName: string;
  jobType: "post_discovery" | "comment_refresh" | "reconciliation" | "analysis";
  status: RunStatus;
  startedAt: string;
  finishedAt?: string;
  fetched: number;
  inserted: number;
  updated: number;
  skipped: number;
  error?: string;
}

export interface WorkbenchData {
  sources: Source[];
  complaints: Complaint[];
  clusters: ProblemCluster[];
  opportunities: Opportunity[];
  ideas: StartupIdea[];
  runs: PipelineRun[];
}
