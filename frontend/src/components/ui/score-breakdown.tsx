import type { ScoreBreakdown as ScoreBreakdownType } from "@/types/domain";

const components: Array<[keyof ScoreBreakdownType, string]> = [
  ["frequency", "Frequency"],
  ["severity", "Severity"],
  ["willingnessToPay", "WTP"],
  ["urgency", "Urgency"],
  ["marketPull", "Market"],
];

export function ScoreBreakdown({ score }: { score: ScoreBreakdownType }) {
  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">Weighted score</p>
          <p className="text-3xl font-semibold text-blue-200">{score.finalScore.toFixed(2)}</p>
        </div>
        <code className="rounded-lg bg-muted px-2 py-1 text-xs text-muted-foreground">{score.formula}</code>
      </div>
      {components.map(([key, label]) => {
        const value = Number(score[key]);
        return (
          <div key={key}>
            <div className="mb-1 flex justify-between text-xs text-muted-foreground">
              <span>{label}</span>
              <span>{value.toFixed(1)} / 5</span>
            </div>
            <div className="h-2 rounded-full bg-muted">
              <div className="h-2 rounded-full bg-primary" style={{ width: `${(value / 5) * 100}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
