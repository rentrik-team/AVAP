import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { dashboardKeys } from "@/features/dashboard/hooks/query-keys";
import { riskApi } from "@/features/risk/api/risk-api";
import { riskKeys } from "@/features/risk/hooks/query-keys";
import type { RiskAssessmentResponse, RiskListFilters } from "@/features/risk/types/risk";
import type { ApiError } from "@/lib/api/errors";

/**
 * Risk assessments are deterministic, backend-calculated records — no
 * polling. Refresh is driven entirely by the calculation mutation's
 * targeted invalidation below, never by a timer.
 */
export function useRiskAssessments(
  params: { skip?: number; limit?: number } & RiskListFilters = {}
) {
  const query = {
    skip: params.skip ?? 0,
    limit: params.limit ?? 50,
    scope: params.scope,
    risk_level: params.risk_level,
  };
  return useQuery({
    queryKey: riskKeys.list(query),
    queryFn: () => riskApi.getRiskAssessments(query),
  });
}

export function useRiskSummary() {
  return useQuery({
    queryKey: riskKeys.summary(),
    queryFn: () => riskApi.getRiskSummary(),
  });
}

export function useScanRisk(scanId: string) {
  return useQuery({
    queryKey: riskKeys.scan(scanId),
    queryFn: () => riskApi.getRiskByScan(scanId),
    enabled: Boolean(scanId),
  });
}

/**
 * No `retry`: recalculation is a real backend write (upserts scope/entity
 * rows in place) — a transport failure after the backend already applied
 * it must not be silently replayed.
 *
 * Cache invalidation is derived from reading the actual Module 09
 * aggregation queries (app/services/dashboard_service.py +
 * app/repositories/dashboard_repository.py), not assumed:
 *
 * - dashboard/summary: `overall_risk_score`/`overall_risk_level` come from
 *   `risk_repository.get_assessment()` (the ASSESSMENT-scope singleton this
 *   mutation just recomputed); `high_risk_asset_count` comes from
 *   `get_asset_risk_level_distribution()` (ASSET-scope rows this mutation
 *   just wrote). Both affected.
 * - dashboard/risk: entirely risk-sourced (`get_assessment()`,
 *   `get_asset_risk_level_distribution()`, `get_top_risk_assets/vulnerabilities`).
 *   Affected.
 * - dashboard/ai: `get_remediation_coverage_counts()` counts VULNERABILITY-scope
 *   risk_assessments (eligible) and correlates
 *   `AIRecommendation.generated_at >= RiskAssessment.calculated_at` (current)
 *   — recalculation bumps `calculated_at`, which can flip a previously
 *   "current" recommendation to stale and change both counts. Affected.
 * - dashboard/assets, dashboard/vulnerabilities, dashboard/scans,
 *   dashboard/reports: none of their queries touch risk_assessments or
 *   ai_recommendations at all (verified by reading each method). NOT invalidated.
 * - The AI feature's own recommendation cache is NOT invalidated here: no
 *   AIRecommendation row is touched by risk calculation. Freshness is
 *   recomputed purely from the (now-refetched) risk assessment's
 *   `calculated_at`, passed down as a prop — see features/ai.
 */
export function useCalculateRiskForScan() {
  const queryClient = useQueryClient();
  return useMutation<RiskAssessmentResponse, ApiError, string>({
    mutationFn: (scanId: string) => riskApi.calculateRiskForScan(scanId),
    onSuccess: (data, scanId) => {
      queryClient.invalidateQueries({ queryKey: riskKeys.lists() });
      queryClient.invalidateQueries({ queryKey: riskKeys.summary() });
      queryClient.setQueryData(riskKeys.scan(scanId), data);
      queryClient.invalidateQueries({ queryKey: dashboardKeys.summary() });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "risk"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "ai"] });
    },
  });
}
