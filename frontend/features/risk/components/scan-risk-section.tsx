"use client";

import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RiskLevelBadge } from "@/components/shared/risk-level-badge";
import { RiskScore } from "@/components/shared/risk-score";
import { Skeleton } from "@/components/ui/skeleton";
import { useCalculateRiskForScan, useScanRisk } from "@/features/risk/hooks/use-risk";
import type { ScanStatus } from "@/features/scans/types/scan";
import { formatRelativeTime } from "@/utils/format";

/**
 * The single, deliberate Risk touchpoint on the Scan Detail page (Phase 05,
 * unmodified otherwise) — the only place "Calculate Risk" is exposed,
 * because scan_id is only ever unambiguously available here. Not
 * duplicated onto every Scan list row or the Risk page itself.
 */
export function ScanRiskSection({
  scanId,
  scanStatus,
}: {
  scanId: string;
  scanStatus: ScanStatus;
}) {
  const { data: risk, isPending, isError } = useScanRisk(scanId);
  const { mutate, isPending: isCalculating } = useCalculateRiskForScan();

  // Calculating risk before a scan has completed findings would only ever
  // produce a trivial/zero result — restrained by the frontend, not a
  // backend rule (the endpoint itself has no status precondition).
  const canCalculate = scanStatus === "COMPLETED";

  function handleCalculate() {
    if (isCalculating) return;
    mutate(scanId, {
      onSuccess: () => toast.success("Risk calculated"),
      onError: (error) => toast.error(error.message),
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk Assessment</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {isPending ? (
          <Skeleton className="h-8 w-40" />
        ) : isError || !risk ? (
          <p className="text-sm text-muted-foreground">
            {canCalculate
              ? "Risk has not been calculated for this scan yet."
              : "Risk can be calculated once this scan completes."}
          </p>
        ) : (
          <div className="flex flex-wrap items-center gap-3">
            <RiskScore score={risk.risk_score} className="text-h3" />
            <RiskLevelBadge level={risk.risk_level} />
            <span className="text-xs text-muted-foreground">
              Calculated {formatRelativeTime(risk.calculated_at)}
            </span>
          </div>
        )}

        {canCalculate && (
          <Button
            variant="outline"
            size="sm"
            className="w-fit"
            onClick={handleCalculate}
            disabled={isCalculating}
          >
            {isCalculating
              ? "Calculating…"
              : risk
                ? "Recalculate Risk"
                : "Calculate Risk"}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
