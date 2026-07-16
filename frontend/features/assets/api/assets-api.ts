import { apiClient } from "@/lib/api/client";
import { requestData, requestVoid } from "@/lib/api/request";
import type { ApiSuccessEnvelope } from "@/types/api";

import type {
  AssetDetailResponse,
  AssetListFilters,
  AssetListResponse,
} from "@/features/assets/types/asset";

/**
 * Thin, typed wrappers around GET/DELETE /api/v1/assets/*. Sole caller of
 * `apiClient` for assets — hooks never call Axios directly. There is no
 * create/update endpoint (Assets are written only by the scan inventory
 * pipeline), so no such function exists here.
 */
export const assetsApi = {
  getAssets: (params: { skip?: number; limit?: number } & AssetListFilters = {}) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<AssetListResponse>>("/assets", { params })
    ),

  getAsset: (assetId: string) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<AssetDetailResponse>>(`/assets/${assetId}`)
    ),

  deleteAsset: (assetId: string) => requestVoid(apiClient.delete(`/assets/${assetId}`)),
};
