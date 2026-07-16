import type { AxiosResponse } from "axios";

import { normalizeApiError } from "@/lib/api/errors";
import type { ApiSuccessEnvelope } from "@/types/api";

/**
 * Explicit response-unwrapping helper used by every feature service
 * function — never a hidden Axios interceptor. Extracts `data.data` from
 * the standardized success envelope and converts any failure into a
 * normalized ApiError.
 */
export async function requestData<T>(
  requestPromise: Promise<AxiosResponse<ApiSuccessEnvelope<T>>>
): Promise<T> {
  try {
    const response = await requestPromise;
    return response.data.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

/**
 * Same error normalization as `requestData`, for endpoints that return
 * `204 No Content` (no envelope body) — e.g. DELETE /targets/{id},
 * DELETE /scans/{id}.
 */
export async function requestVoid(
  requestPromise: Promise<AxiosResponse<unknown>>
): Promise<void> {
  try {
    await requestPromise;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
