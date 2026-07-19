import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { dashboardKeys } from "@/features/dashboard/hooks/query-keys";
import { scansApi } from "@/features/scans/api/scans-api";
import { scanKeys } from "@/features/scans/hooks/query-keys";
import type {
  CreateScanRequest,
  ScanResponse,
  ScanStatus,
} from "@/features/scans/types/scan";
import type { ApiError } from "@/lib/api/errors";

/**
 * Backend_Walk.md §10.7: poll GET /scans/{id}/status (cheap, single-row
 * lookup) rather than the full GET /scans/{id}. No explicit interval is
 * documented for this endpoint specifically, so this uses the low end of
 * the one explicitly documented "safe to poll" bound in this codebase
 * (§10.6, 10-30s for the even-heavier /dashboard/* aggregates) rather than
 * inventing an unsupported faster cadence.
 */
export const SCAN_STATUS_POLL_INTERVAL_MS = 10_000;

export function isTerminalScanStatus(status: ScanStatus): boolean {
  return (
    status === "COMPLETED" || status === "FAILED" || status === "CANCELLED"
  );
}

/** Pure so the stop-on-terminal / poll-while-active decision is unit-testable. */
export function resolveScanStatusPollInterval(
  status: ScanStatus | undefined
): number | false {
  if (!status || isTerminalScanStatus(status)) return false;
  return SCAN_STATUS_POLL_INTERVAL_MS;
}

/** Same status-aware rule applied to a page of scans: poll only while at
 * least one row in the current page is still PENDING/RUNNING. */
export function resolveScanListPollInterval(
  scans: ScanResponse[] | undefined
): number | false {
  if (!scans || scans.length === 0) return false;
  const hasActiveScan = scans.some((scan) => !isTerminalScanStatus(scan.status));
  return hasActiveScan ? SCAN_STATUS_POLL_INTERVAL_MS : false;
}

export function useScans(
  params: { skip?: number; limit?: number; target_id?: string } = {}
) {
  const skip = params.skip ?? 0;
  const limit = params.limit ?? 50;
  const query = { skip, limit, target_id: params.target_id };
  return useQuery({
    queryKey: scanKeys.list(query),
    queryFn: () => scansApi.getScans(query),
    refetchInterval: (query) =>
      resolveScanListPollInterval(query.state.data?.scans),
  });
}

/** One-shot full detail fetch. Lifecycle observation is `useScanStatus`'s job. */
export function useScan(scanId: string) {
  return useQuery({
    queryKey: scanKeys.detail(scanId),
    queryFn: () => scansApi.getScan(scanId),
    enabled: Boolean(scanId),
  });
}

/** Status-aware polling of the lightweight status endpoint; stops once terminal. */
export function useScanStatus(scanId: string) {
  return useQuery({
    queryKey: scanKeys.status(scanId),
    queryFn: () => scansApi.getScanStatus(scanId),
    enabled: Boolean(scanId),
    refetchInterval: (query) => resolveScanStatusPollInterval(query.state.data?.status),
  });
}

/**
 * No `retry`: scan creation is not idempotent and the API contract offers
 * no idempotency key — a transport failure after the backend already
 * dispatched a scan must not be silently replayed.
 */
export function useCreateScan() {
  const queryClient = useQueryClient();
  return useMutation<ScanResponse, ApiError, CreateScanRequest>({
    mutationFn: (body: CreateScanRequest) => scansApi.createScan(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scanKeys.lists() });
      queryClient.invalidateQueries({ queryKey: dashboardKeys.summary() });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "scans"] });
    },
  });
}

/**
 * No `retry`: cancellation is not idempotent to replay blindly — a retry
 * after a transport failure could hit a scan that has since finished on
 * its own and get back a stale-looking conflict.
 */
export function useCancelScan() {
  const queryClient = useQueryClient();
  return useMutation<ScanResponse, ApiError, string>({
    mutationFn: (scanId: string) => scansApi.cancelScan(scanId),
    onSuccess: (_data, scanId) => {
      queryClient.invalidateQueries({ queryKey: scanKeys.detail(scanId) });
      queryClient.invalidateQueries({ queryKey: scanKeys.status(scanId) });
      queryClient.invalidateQueries({ queryKey: scanKeys.lists() });
      queryClient.invalidateQueries({ queryKey: dashboardKeys.summary() });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "scans"] });
    },
  });
}

/** No `retry`: delete is not safely replayable without idempotency support. */
export function useDeleteScan() {
  const queryClient = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: (scanId: string) => scansApi.deleteScan(scanId),
    onSuccess: (_data, scanId) => {
      queryClient.invalidateQueries({ queryKey: scanKeys.lists() });
      queryClient.removeQueries({ queryKey: scanKeys.detail(scanId) });
      queryClient.removeQueries({ queryKey: scanKeys.status(scanId) });
      queryClient.invalidateQueries({ queryKey: dashboardKeys.summary() });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "scans"] });
    },
  });
}
