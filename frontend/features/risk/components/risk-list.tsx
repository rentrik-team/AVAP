"use client";

import { Gauge, ShieldOff } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { ListRowsSkeleton } from "@/components/shared/skeletons";
import { RiskCards } from "@/features/risk/components/risk-cards";
import { RiskFilterBar } from "@/features/risk/components/risk-filter-bar";
import { RiskTable } from "@/features/risk/components/risk-table";
import { VulnerabilityRiskSheet } from "@/features/risk/components/vulnerability-risk-sheet";
import { useRiskAssessments } from "@/features/risk/hooks/use-risk";
import type {
  RiskAssessmentResponse,
  RiskLevel,
  RiskListFilters,
  RiskScope,
} from "@/features/risk/types/risk";
import { formatCount } from "@/utils/format";

const PAGE_SIZE = 50;

export function RiskList() {
  const [skip, setSkip] = useState(0);
  const [scope, setScope] = useState<RiskScope | "">("");
  const [riskLevel, setRiskLevel] = useState<RiskLevel | "">("");
  const [appliedFilters, setAppliedFilters] = useState<RiskListFilters>({});
  const [remediationTarget, setRemediationTarget] =
    useState<RiskAssessmentResponse | null>(null);

  const hasActiveFilters = Boolean(scope || riskLevel);

  const filters: RiskListFilters = {
    scope: scope || undefined,
    risk_level: riskLevel || undefined,
  };

  // Reset to the first page whenever the active filter set changes —
  // adjusted during render, not in a useEffect (see AssetList precedent).
  if (
    filters.scope !== appliedFilters.scope ||
    filters.risk_level !== appliedFilters.risk_level
  ) {
    setAppliedFilters(filters);
    setSkip(0);
  }

  const { data, isPending, isError, refetch } = useRiskAssessments({
    skip,
    limit: PAGE_SIZE,
    ...filters,
  });

  function handleFilterChange(next: RiskListFilters) {
    setScope(next.scope ?? "");
    setRiskLevel(next.risk_level ?? "");
  }

  function handleClearFilters() {
    setScope("");
    setRiskLevel("");
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <RiskFilterBar scope={scope} riskLevel={riskLevel} onFilterChange={handleFilterChange} />
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground"
            onClick={handleClearFilters}
          >
            Clear filters
          </Button>
        )}
      </div>

      {isPending ? (
        <ListRowsSkeleton rows={6} />
      ) : isError ? (
        <ErrorState
          title="Unable to load risk assessments"
          description="Risk data could not be retrieved."
          onRetry={() => refetch()}
        />
      ) : data.risk_assessments.length === 0 ? (
        hasActiveFilters ? (
          <EmptyState
            icon={ShieldOff}
            title="No risk assessments match these filters"
            description="Clear or adjust the active filters to see more results."
          />
        ) : (
          <EmptyState
            icon={Gauge}
            title="No risk assessments have been calculated yet"
            description="Risk is calculated explicitly for a completed scan from that scan's detail page. Once calculated, results appear here."
          />
        )
      ) : (
        <>
          <RiskTable
            assessments={data.risk_assessments}
            onOpenRemediation={setRemediationTarget}
          />
          <RiskCards
            assessments={data.risk_assessments}
            onOpenRemediation={setRemediationTarget}
          />

          <div className="flex items-center justify-between gap-4">
            <p className="text-sm text-muted-foreground">
              Showing {formatCount(skip + 1)}–
              {formatCount(Math.min(skip + PAGE_SIZE, data.total))} of{" "}
              {formatCount(data.total)}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSkip((prev) => Math.max(prev - PAGE_SIZE, 0))}
                disabled={skip === 0}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSkip((prev) => prev + PAGE_SIZE)}
                disabled={skip + PAGE_SIZE >= data.total}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}

      <VulnerabilityRiskSheet
        assessment={remediationTarget}
        open={Boolean(remediationTarget)}
        onOpenChange={(next) => {
          if (!next) setRemediationTarget(null);
        }}
      />
    </div>
  );
}
