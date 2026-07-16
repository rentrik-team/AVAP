"use client";

import { Gauge } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { RiskLevelBadge } from "@/components/shared/risk-level-badge";
import { RiskScore } from "@/components/shared/risk-score";
import { Skeleton } from "@/components/ui/skeleton";
import { useRiskSummary } from "@/features/risk/hooks/use-risk";
import { ApiError } from "@/lib/api/errors";
import { formatRelativeTime } from "@/utils/format";

/** GET /risk/summary is the singleton ASSESSMENT-scope record — the
 * authoritative platform-wide risk read model. Never recomputed from the
 * Risk list on the client. */
export function RiskSummaryCard() {
  const { data: summary, isPending, isError, error, refetch } = useRiskSummary();

  if (isPending) {
    return (
      <Card className="col-span-full rounded-xl lg:col-span-8">
        <CardContent className="flex flex-col gap-4">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-10 w-32" />
        </CardContent>
      </Card>
    );
  }

  const isMissing = isError && error instanceof ApiError && error.code === "NOT_FOUND";

  if (isMissing) {
    return (
      <Card className="col-span-full rounded-xl lg:col-span-8">
        <CardContent>
          <EmptyState
            icon={Gauge}
            title="No risk assessment yet"
            description="Calculate risk for a completed scan to see the platform-wide summary here."
          />
        </CardContent>
      </Card>
    );
  }

  if (isError || !summary) {
    return (
      <Card className="col-span-full rounded-xl lg:col-span-8">
        <CardContent>
          <ErrorState
            title="Unable to load the risk summary"
            description="Platform risk data could not be retrieved."
            onRetry={() => refetch()}
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="col-span-full overflow-hidden rounded-xl border-primary/15 bg-gradient-to-br from-accent/40 via-card to-card lg:col-span-8">
      <CardContent className="flex h-full flex-col gap-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">
            Overall Platform Risk
          </span>
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Gauge className="size-4.5" aria-hidden="true" />
          </span>
        </div>

        <div className="flex items-end gap-3">
          <RiskScore score={summary.risk_score} className="text-h1" />
          <RiskLevelBadge level={summary.risk_level} className="mb-1.5" />
        </div>

        <p className="mt-auto text-xs text-muted-foreground">
          Calculated {formatRelativeTime(summary.calculated_at)} · v
          {summary.calculation_version}
        </p>
      </CardContent>
    </Card>
  );
}
