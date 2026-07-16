import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { dashboardKeys } from "@/features/dashboard/hooks/query-keys";
import { reportsApi } from "@/features/reports/api/reports-api";
import { reportKeys } from "@/features/reports/hooks/query-keys";
import type { ReportListFilters, ReportResponse } from "@/features/reports/types/report";
import type { ApiError } from "@/lib/api/errors";

/** Reports are immutable, generated-on-demand artifacts — no polling. */
export function useReports(params: { skip?: number; limit?: number } & ReportListFilters = {}) {
  const query = {
    skip: params.skip ?? 0,
    limit: params.limit ?? 50,
    scan_id: params.scan_id,
  };
  return useQuery({
    queryKey: reportKeys.list(query),
    queryFn: () => reportsApi.getReports(query),
  });
}

export function useReport(reportId: string) {
  return useQuery({
    queryKey: reportKeys.detail(reportId),
    queryFn: () => reportsApi.getReport(reportId),
    enabled: Boolean(reportId),
  });
}

/**
 * No `retry`: every successful call creates a brand-new immutable report
 * row and file (never overwrites) — replaying a request whose response was
 * merely lost in transit would create a duplicate report, not recover one.
 *
 * Invalidation verified against app/services/dashboard_service.py: report
 * generation only ever touches the `reports` table, so `dashboard/reports`
 * (total/format breakdown/recent list) and `dashboard/summary`
 * (total_reports_generated) are affected; no risk/AI/asset/vulnerability/
 * scan read model is touched (ReportService only *reads* risk/AI data —
 * confirmed in report_service.py, which calls no risk/AI write method).
 */
export function useGenerateReport() {
  const queryClient = useQueryClient();
  return useMutation<ReportResponse, ApiError, string>({
    mutationFn: (scanId: string) => reportsApi.generateReport(scanId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reportKeys.lists() });
      queryClient.invalidateQueries({ queryKey: dashboardKeys.summary() });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "reports"] });
    },
  });
}

/** No `retry`: delete is not safely replayable without idempotency support. */
export function useDeleteReport() {
  const queryClient = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: (reportId: string) => reportsApi.deleteReport(reportId),
    onSuccess: (_data, reportId) => {
      queryClient.invalidateQueries({ queryKey: reportKeys.lists() });
      queryClient.removeQueries({ queryKey: reportKeys.detail(reportId) });
      queryClient.invalidateQueries({ queryKey: dashboardKeys.summary() });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "reports"] });
    },
  });
}

/**
 * A user-triggered download action, not cacheable server state — modeled
 * as a mutation (like Scan/Risk/AI action triggers) rather than a query.
 * No cache effect: downloading doesn't change any persisted read model.
 */
export function useDownloadReport() {
  return useMutation<Blob, ApiError, string>({
    mutationFn: (reportId: string) => reportsApi.downloadReport(reportId),
  });
}
