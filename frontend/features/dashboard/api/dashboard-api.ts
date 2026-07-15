import { apiClient } from "@/lib/api/client";
import { requestData } from "@/lib/api/request";
import type { ApiSuccessEnvelope } from "@/types/api";

import type {
  DashboardAIStatisticsResponse,
  DashboardAssetStatisticsResponse,
  DashboardReportStatisticsResponse,
  DashboardRiskStatisticsResponse,
  DashboardScanStatisticsResponse,
  DashboardSummaryResponse,
  DashboardVulnerabilityStatisticsResponse,
} from "@/features/dashboard/types/dashboard";

/**
 * Thin, typed wrappers around GET /api/v1/dashboard/*. Every function here
 * is the sole caller of `apiClient` for its endpoint — hooks never call
 * Axios directly. All seven endpoints are read-only (see
 * modules_docs/09_dashboard.md); none of these ever mutate or trigger
 * calculation/generation.
 */
export const dashboardApi = {
  getSummary: () =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<DashboardSummaryResponse>>(
        "/dashboard/summary"
      )
    ),

  getAssetStatistics: (limit = 10) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<DashboardAssetStatisticsResponse>>(
        "/dashboard/assets",
        { params: { limit } }
      )
    ),

  getVulnerabilityStatistics: () =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<DashboardVulnerabilityStatisticsResponse>>(
        "/dashboard/vulnerabilities"
      )
    ),

  getRiskStatistics: (topLimit = 10) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<DashboardRiskStatisticsResponse>>(
        "/dashboard/risk",
        { params: { top_limit: topLimit } }
      )
    ),

  getScanStatistics: (limit = 10) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<DashboardScanStatisticsResponse>>(
        "/dashboard/scans",
        { params: { limit } }
      )
    ),

  getReportStatistics: (limit = 10) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<DashboardReportStatisticsResponse>>(
        "/dashboard/reports",
        { params: { limit } }
      )
    ),

  getAIStatistics: () =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<DashboardAIStatisticsResponse>>("/dashboard/ai")
    ),
};
