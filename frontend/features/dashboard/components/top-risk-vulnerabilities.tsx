"use client";

import { Bug } from "lucide-react";

import { CopyableValue } from "@/components/shared/copyable-value";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { RiskLevelBadge } from "@/components/shared/risk-level-badge";
import { RiskScore } from "@/components/shared/risk-score";
import { ListRowsSkeleton } from "@/components/shared/skeletons";
import { useDashboardRiskStatistics } from "@/features/dashboard/hooks/use-dashboard";

export function TopRiskVulnerabilities() {
  const { data, isPending, isError, refetch } = useDashboardRiskStatistics();

  if (isPending) return <ListRowsSkeleton />;

  if (isError) {
    return (
      <ErrorState
        title="Unable to load top-risk vulnerabilities"
        description="Risk ranking data could not be retrieved."
        onRetry={() => refetch()}
      />
    );
  }

  if (data.top_risk_vulnerabilities.length === 0) {
    return (
      <EmptyState
        icon={Bug}
        title="No vulnerabilities ranked yet"
        description="Top-risk vulnerabilities appear once risk has been calculated for a scan."
      />
    );
  }

  return (
    <ul className="flex flex-col divide-y divide-border">
      {data.top_risk_vulnerabilities.map((vulnerability) => (
        <li
          key={vulnerability.vulnerability_id}
          className="flex items-center justify-between gap-3 py-2.5"
        >
          <div className="flex min-w-0 flex-col">
            <span className="truncate text-sm text-foreground">{vulnerability.name}</span>
            <div className="flex items-center gap-2">
              {vulnerability.cve && (
                <CopyableValue value={vulnerability.cve} className="text-xs" />
              )}
              <span className="text-xs text-muted-foreground">
                {vulnerability.affected_asset_count} affected asset
                {vulnerability.affected_asset_count === 1 ? "" : "s"}
              </span>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <RiskScore score={vulnerability.risk_score} />
            <RiskLevelBadge level={vulnerability.risk_level} />
          </div>
        </li>
      ))}
    </ul>
  );
}
