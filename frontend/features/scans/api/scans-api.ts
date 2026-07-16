import { apiClient } from "@/lib/api/client";
import { requestData, requestVoid } from "@/lib/api/request";
import type { ApiSuccessEnvelope } from "@/types/api";

import type {
  CreateScanRequest,
  ScanListResponse,
  ScanResponse,
  ScanStatusResponse,
} from "@/features/scans/types/scan";

/**
 * Thin, typed wrappers around GET/POST/DELETE /api/v1/scans/*. Sole caller
 * of `apiClient` for scans — hooks never call Axios directly.
 */
export const scansApi = {
  getScans: (params: { skip?: number; limit?: number } = {}) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<ScanListResponse>>("/scans", { params })
    ),

  getScan: (scanId: string) =>
    requestData(apiClient.get<ApiSuccessEnvelope<ScanResponse>>(`/scans/${scanId}`)),

  getScanStatus: (scanId: string) =>
    requestData(
      apiClient.get<ApiSuccessEnvelope<ScanStatusResponse>>(
        `/scans/${scanId}/status`
      )
    ),

  createScan: (body: CreateScanRequest) =>
    requestData(apiClient.post<ApiSuccessEnvelope<ScanResponse>>("/scans", body)),

  deleteScan: (scanId: string) => requestVoid(apiClient.delete(`/scans/${scanId}`)),
};
