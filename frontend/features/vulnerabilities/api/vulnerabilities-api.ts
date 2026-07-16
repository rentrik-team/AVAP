import { apiClient } from "@/lib/api/client";
import { requestData } from "@/lib/api/request";
import type { ApiSuccessEnvelope } from "@/types/api";

import type {
  VulnerabilityListFilters,
  VulnerabilityListResponse,
  VulnerabilityResponse,
} from "@/features/vulnerabilities/types/vulnerability";

/**
 * Thin, typed wrappers around GET /api/v1/vulnerabilities/*. Sole caller of
 * `apiClient` for vulnerabilities. The Vulnerability API is read-only — no
 * create/update/delete endpoint exists, so no such functions are defined
 * here.
 */
export const vulnerabilitiesApi = {
  getVulnerabilities: (
    params: { skip?: number; limit?: number } & VulnerabilityListFilters = {}
  ) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<VulnerabilityListResponse>>(
        "/vulnerabilities",
        { params }
      )
    ),

  getVulnerability: (vulnerabilityId: string) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<VulnerabilityResponse>>(
        `/vulnerabilities/${vulnerabilityId}`
      )
    ),
};
