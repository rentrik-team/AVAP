import { apiClient } from "@/lib/api/client";
import { requestData, requestVoid } from "@/lib/api/request";
import type { ApiSuccessEnvelope } from "@/types/api";

import type {
  CreateTargetRequest,
  TargetListResponse,
  TargetResponse,
} from "@/features/targets/types/target";

/**
 * Thin, typed wrappers around GET/POST/DELETE /api/v1/targets/*. This is the
 * sole caller of `apiClient` for targets — hooks never call Axios directly.
 * PUT /targets/{id} (update) exists on the backend but is intentionally not
 * wrapped here: editing an existing target is out of scope for this phase.
 */
export const targetsApi = {
  getTargets: (params: { skip?: number; limit?: number } = {}) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<TargetListResponse>>("/targets", {
        params,
      })
    ),

  getTarget: (targetId: string) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<TargetResponse>>(`/targets/${targetId}`)
    ),

  createTarget: (body: CreateTargetRequest) =>
    requestData(
      apiClient.post<ApiSuccessEnvelope<TargetResponse>>("/targets", body)
    ),

  deleteTarget: (targetId: string) =>
    requestVoid(apiClient.delete(`/targets/${targetId}`)),
};
