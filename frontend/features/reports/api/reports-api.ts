import { apiClient } from "@/lib/api/client";
import { normalizeApiError } from "@/lib/api/errors";
import { requestData, requestVoid } from "@/lib/api/request";
import type { ApiSuccessEnvelope } from "@/types/api";

import type {
  ReportListFilters,
  ReportListResponse,
  ReportResponse,
} from "@/features/reports/types/report";

/**
 * Thin, typed wrappers around GET/POST/DELETE /api/v1/reports/*. Sole
 * caller of `apiClient` for reports — hooks never call Axios directly.
 * Reports are generated for a specific scan and never regenerated
 * automatically (no polling, no auto risk/AI triggering) — every function
 * here maps 1:1 to a single explicit backend call.
 */
export const reportsApi = {
  getReports: (params: { skip?: number; limit?: number } & ReportListFilters = {}) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<ReportListResponse>>("/reports", { params })
    ),

  getReport: (reportId: string) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<ReportResponse>>(`/reports/${reportId}`)
    ),

  generateReport: (scanId: string) =>
    requestData(
      apiClient.post<ApiSuccessEnvelope<ReportResponse>>("/reports", {
        scan_id: scanId,
      })
    ),

  deleteReport: (reportId: string) =>
    requestVoid(apiClient.delete(`/reports/${reportId}`)),

  /**
   * GET /reports/{id}/download returns raw PDF bytes with
   * Content-Type: application/pdf — not the standard SuccessResponse
   * envelope, so this bypasses `requestData` (which assumes an envelope)
   * but still goes through the same centralized `apiClient` and the same
   * `normalizeApiError` failure path as every other call.
   */
  downloadReport: async (reportId: string): Promise<Blob> => {
    try {
      const response = await apiClient.get<Blob>(`/reports/${reportId}/download`, {
        responseType: "blob",
      });
      return response.data;
    } catch (error) {
      throw normalizeApiError(error);
    }
  },
};
