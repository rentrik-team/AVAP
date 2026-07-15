"use client";

import { ShieldOff } from "lucide-react";

import { CopyableValue } from "@/components/shared/copyable-value";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { RiskLevelBadge } from "@/components/shared/risk-level-badge";
import { RiskScore } from "@/components/shared/risk-score";
import { ListRowsSkeleton } from "@/components/shared/skeletons";
import { useDashboardRiskStatistics } from "@/features/dashboard/hooks/use-dashboard";

export function TopRiskAssets() {
  const { data, isPending, isError, refetch } = useDashboardRiskStatistics();

  if (isPending) return <ListRowsSkeleton />;

  if (isError) {
    return (
      <ErrorState
        title="Unable to load top-risk assets"
        description="Risk ranking data could not be retrieved."
        onRetry={() => refetch()}
      />
    );
  }

  if (data.top_risk_assets.length === 0) {
    return (
      <EmptyState
        icon={ShieldOff}
        title="No assets ranked yet"
        description="Top-risk assets appear once risk has been calculated for a scan."
      />
    );
  }

  return (
    <ul className="flex flex-col divide-y divide-border">
      {data.top_risk_assets.map((asset) => (
        <li key={asset.asset_id} className="flex items-center justify-between gap-3 py-2.5">
          <div className="flex min-w-0 flex-col">
            <CopyableValue value={asset.ipv4} className="text-sm" />
            {asset.hostname && (
              <span className="truncate text-xs text-muted-foreground">
                {asset.hostname}
              </span>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <RiskScore score={asset.risk_score} />
            <RiskLevelBadge level={asset.risk_level} />
          </div>
        </li>
      ))}
    </ul>
  );
}
