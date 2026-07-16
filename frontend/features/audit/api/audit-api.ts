import { apiClient } from "@/lib/api/client";
import { requestData } from "@/lib/api/request";
import type { ApiSuccessEnvelope } from "@/types/api";

import type {
  AuditEventListFilters,
  AuditEventListResponse,
} from "@/features/audit/types/audit";

/**
 * Thin, typed wrapper around GET /api/v1/audit. Sole caller of `apiClient`
 * for audit — hooks never call Axios directly. There is deliberately no
 * `getAuditEvent(id)` wrapper: the list response already returns the full
 * `AuditEventResponse` per row, so the detail drawer is given the
 * already-fetched row object as a prop rather than issuing a second fetch
 * for data it already has (GET /audit/{id} exists and is backend-tested,
 * but has no frontend consumer in this phase).
 */
export const auditApi = {
  getAuditEvents: (
    params: { skip?: number; limit?: number } & AuditEventListFilters = {}
  ) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<AuditEventListResponse>>("/audit", {
        params,
      })
    ),
};
