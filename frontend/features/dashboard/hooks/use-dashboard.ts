import { useQuery } from "@tanstack/react-query";

import { dashboardApi } from "@/features/dashboard/api/dashboard-api";
import { dashboardKeys } from "@/features/dashboard/hooks/query-keys";

/**
 * All seven /dashboard/* endpoints are cheap, bounded, read-only aggregate
 * queries explicitly documented as safe to poll every 10–30s (see
 * Backend_Walk.md §10.6). 30s balances a "live" dashboard against request
 * volume — none of these calls ever trigger calculation/generation.
 */
const DASHBOARD_POLL_INTERVAL_MS = 30_000;

export function useDashboardSummary() {
  return useQuery({
    queryKey: dashboardKeys.summary(),
    queryFn: dashboardApi.getSummary,
    refetchInterval: DASHBOARD_POLL_INTERVAL_MS,
  });
}

export function useDashboardAssetStatistics(limit = 10) {
  return useQuery({
    queryKey: dashboardKeys.assets(limit),
    queryFn: () => dashboardApi.getAssetStatistics(limit),
    refetchInterval: DASHBOARD_POLL_INTERVAL_MS,
  });
}

export function useDashboardVulnerabilityStatistics() {
  return useQuery({
    queryKey: dashboardKeys.vulnerabilities(),
    queryFn: dashboardApi.getVulnerabilityStatistics,
    refetchInterval: DASHBOARD_POLL_INTERVAL_MS,
  });
}

export function useDashboardRiskStatistics(topLimit = 10) {
  return useQuery({
    queryKey: dashboardKeys.risk(topLimit),
    queryFn: () => dashboardApi.getRiskStatistics(topLimit),
    refetchInterval: DASHBOARD_POLL_INTERVAL_MS,
  });
}

export function useDashboardScanStatistics(limit = 10) {
  return useQuery({
    queryKey: dashboardKeys.scans(limit),
    queryFn: () => dashboardApi.getScanStatistics(limit),
    refetchInterval: DASHBOARD_POLL_INTERVAL_MS,
  });
}

export function useDashboardReportStatistics(limit = 10) {
  return useQuery({
    queryKey: dashboardKeys.reports(limit),
    queryFn: () => dashboardApi.getReportStatistics(limit),
    refetchInterval: DASHBOARD_POLL_INTERVAL_MS,
  });
}

export function useDashboardAIStatistics() {
  return useQuery({
    queryKey: dashboardKeys.ai(),
    queryFn: dashboardApi.getAIStatistics,
    refetchInterval: DASHBOARD_POLL_INTERVAL_MS,
  });
}
