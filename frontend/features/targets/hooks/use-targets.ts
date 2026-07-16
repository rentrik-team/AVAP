import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { dashboardKeys } from "@/features/dashboard/hooks/query-keys";
import { targetsApi } from "@/features/targets/api/targets-api";
import { targetKeys } from "@/features/targets/hooks/query-keys";
import type {
  CreateTargetRequest,
  TargetResponse,
} from "@/features/targets/types/target";
import type { ApiError } from "@/lib/api/errors";

export function useTargets(params: { skip?: number; limit?: number } = {}) {
  const skip = params.skip ?? 0;
  const limit = params.limit ?? 50;
  return useQuery({
    queryKey: targetKeys.list({ skip, limit }),
    queryFn: () => targetsApi.getTargets({ skip, limit }),
  });
}

export function useTarget(targetId: string) {
  return useQuery({
    queryKey: targetKeys.detail(targetId),
    queryFn: () => targetsApi.getTarget(targetId),
    enabled: Boolean(targetId),
  });
}

/**
 * No `retry` option: creation is not idempotent (a transport failure after
 * the backend already persisted the target would create a duplicate on
 * replay), and the API contract offers no idempotency key. Relies on
 * TanStack Query's default mutation behavior of zero automatic retries.
 */
export function useCreateTarget() {
  const queryClient = useQueryClient();
  return useMutation<TargetResponse, ApiError, CreateTargetRequest>({
    mutationFn: (body: CreateTargetRequest) => targetsApi.createTarget(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: targetKeys.lists() });
      queryClient.invalidateQueries({ queryKey: dashboardKeys.summary() });
    },
  });
}

/** No `retry`: delete is not safely replayable without idempotency support. */
export function useDeleteTarget() {
  const queryClient = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: (targetId: string) => targetsApi.deleteTarget(targetId),
    onSuccess: (_data, targetId) => {
      queryClient.invalidateQueries({ queryKey: targetKeys.lists() });
      queryClient.removeQueries({ queryKey: targetKeys.detail(targetId) });
      queryClient.invalidateQueries({ queryKey: dashboardKeys.summary() });
    },
  });
}
