"use client";

import { AlertTriangle, ShieldAlert } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { ErrorState } from "@/components/shared/error-state";
import { RiskLevelBadge } from "@/components/shared/risk-level-badge";
import { RiskScore } from "@/components/shared/risk-score";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardSummary } from "@/features/dashboard/hooks/use-dashboard";
import { formatCount, formatRelativeTime } from "@/utils/format";

export function RiskHero() {
  const { data, isPending, isError, refetch } = useDashboardSummary();

  if (isPending) {
    return (
      <Card className="col-span-full rounded-xl lg:col-span-8">
        <CardContent className="flex flex-col gap-4">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-4 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className="col-span-full rounded-xl lg:col-span-8">
        <CardContent>
          <ErrorState
            title="Unable to load security posture"
            description="Platform risk data could not be retrieved."
            onRetry={() => refetch()}
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="col-span-full overflow-hidden rounded-xl border-primary/15 bg-gradient-to-br from-accent/40 via-card to-card lg:col-span-8">
      <CardContent className="flex h-full flex-col gap-5">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">
            Overall Security Posture
          </span>
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <ShieldAlert className="size-4.5" aria-hidden="true" />
          </span>
        </div>

        <div className="flex items-end gap-3">
          <RiskScore score={data.overall_risk_score} className="text-h1" />
          <RiskLevelBadge level={data.overall_risk_level} className="mb-1.5" />
        </div>

        <div className="mt-auto grid grid-cols-2 gap-4 border-t border-border pt-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="size-4 shrink-0 text-severity-critical" aria-hidden="true" />
            <div className="flex flex-col">
              <span className="font-mono text-lg font-semibold tabular-nums">
                {formatCount(data.critical_vulnerability_count)}
              </span>
              <span className="text-xs text-muted-foreground">Critical vulnerabilities</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="size-4 shrink-0 text-severity-high" aria-hidden="true" />
            <div className="flex flex-col">
              <span className="font-mono text-lg font-semibold tabular-nums">
                {formatCount(data.high_risk_asset_count)}
              </span>
              <span className="text-xs text-muted-foreground">High-risk assets</span>
            </div>
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          Updated {formatRelativeTime(data.generated_at)}
        </p>
      </CardContent>
    </Card>
  );
}
