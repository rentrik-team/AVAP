import { apiClient } from "@/lib/api/client";
import { requestData } from "@/lib/api/request";
import type { ApiSuccessEnvelope } from "@/types/api";

import type { AIRecommendationResponse } from "@/features/ai/types/ai";

/**
 * Thin, typed wrappers around GET/POST /api/v1/ai/recommendations/*. Sole
 * caller of `apiClient` for AI — hooks never call Axios directly. The
 * browser never talks to an AI provider directly; every request goes
 * through this backend endpoint.
 *
 * GET /ai/providers and GET /ai/models exist on the backend but are not
 * wrapped here: the generation endpoint accepts no provider/model
 * selection from the request (it is resolved server-side by AIManager),
 * so there is no UI surface that would consume a provider/model selector,
 * and AIRecommendationResponse already carries the provider/model that
 * actually produced each specific recommendation. Documented as a
 * deliberate omission.
 */
export const aiApi = {
  getRecommendation: (assessmentId: string) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<AIRecommendationResponse>>(
        `/ai/recommendations/${assessmentId}`
      )
    ),

  generateRecommendation: (assessmentId: string) =>
    requestData(
      apiClient.post<ApiSuccessEnvelope<AIRecommendationResponse>>(
        `/ai/recommendations/${assessmentId}/generate`
      )
    ),
};
