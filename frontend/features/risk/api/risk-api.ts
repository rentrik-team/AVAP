import { apiClient } from "@/lib/api/client";
import { requestData } from "@/lib/api/request";
import type { ApiSuccessEnvelope } from "@/types/api";

import type {
  RiskAssessmentListResponse,
  RiskAssessmentResponse,
  RiskListFilters,
} from "@/features/risk/types/risk";

/**
 * Thin, typed wrappers around GET/POST /api/v1/risk/*. Sole caller of
 * `apiClient` for risk — hooks never call Axios directly.
 *
 * GET /risk/assets/{asset_id} (asset risk history) is a real, tested
 * backend endpoint but has no wrapper here: this phase has no page that
 * consumes it (the main Risk list already covers browsing ASSET-scope rows
 * via the scope filter, and Asset Detail — a completed Phase 06 feature —
 * is intentionally not modified in this phase). Documented as a deliberate
 * omission, not an oversight, to avoid an unused/dead API function.
 */
export const riskApi = {
  getRiskAssessments: (
    params: { skip?: number; limit?: number } & RiskListFilters = {}
  ) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<RiskAssessmentListResponse>>("/risk", {
        params,
      })
    ),

  getRiskByScan: (scanId: string) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<RiskAssessmentResponse>>(
        `/risk/scans/${scanId}`
      )
    ),

  calculateRiskForScan: (scanId: string) =>
    requestData(
      apiClient.post<ApiSuccessEnvelope<RiskAssessmentResponse>>(
        `/risk/scans/${scanId}/calculate`
      )
    ),

  getRiskSummary: () =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<RiskAssessmentResponse>>("/risk/summary")
    ),
};
