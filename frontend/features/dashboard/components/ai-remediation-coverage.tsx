"use client";

import { ErrorState } from "@/components/shared/error-state";
import { ChartSkeleton } from "@/components/shared/skeletons";
import { useDashboardAIStatistics } from "@/features/dashboard/hooks/use-dashboard";
import { formatCount, formatPercent } from "@/utils/format";

export function AiRemediationCoverage() {
  const { data, isPending, isError, refetch } = useDashboardAIStatistics();

  if (isPending) return <ChartSkeleton />;

  if (isError) {
    return (
      <ErrorState
        title="Unable to load AI remediation coverage"
        description="AI recommendation availability data could not be retrieved."
        onRetry={() => refetch()}
      />
    );
  }

  const providerEntries = Object.entries(data.recommendations_by_provider);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="flex items-end justify-between">
          <span className="font-mono text-3xl font-semibold tabular-nums text-foreground">
            {formatPercent(data.remediation_coverage_percent)}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatCount(data.current_recommendation_count)} of{" "}
            {formatCount(data.eligible_vulnerability_risk_count)} eligible findings
          </span>
        </div>
        <div
          role="progressbar"
          aria-label="AI remediation recommendation coverage"
          aria-valuenow={Math.round(data.remediation_coverage_percent)}
          aria-valuemin={0}
          aria-valuemax={100}
          className="mt-2 h-2 w-full overflow-hidden rounded-full bg-muted"
        >
          <div
            className="h-full rounded-full bg-primary transition-[width]"
            style={{ width: `${Math.min(data.remediation_coverage_percent, 100)}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 border-t border-border pt-4 text-sm">
        <div className="flex flex-col">
          <span className="text-xs text-muted-foreground">Missing recommendations</span>
          <span className="font-mono font-semibold tabular-nums">
            {formatCount(data.missing_recommendation_count)}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-muted-foreground">Total generated</span>
          <span className="font-mono font-semibold tabular-nums">
            {formatCount(data.total_recommendations)}
          </span>
        </div>
      </div>

      {providerEntries.length > 0 && (
        <div className="flex flex-wrap gap-2 border-t border-border pt-4">
          {providerEntries.map(([provider, count]) => (
            <span
              key={provider}
              className="rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground"
            >
              {provider} · {formatCount(count)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
