import { useQuery } from "@tanstack/react-query";

import { auditApi } from "@/features/audit/api/audit-api";
import { auditKeys } from "@/features/audit/hooks/query-keys";
import type { AuditEventListFilters } from "@/features/audit/types/audit";

/**
 * Audit events are an immutable forensic timeline, not a live operational
 * feed — no polling. There is no mutation hook in this feature at all:
 * the API is read-only (no POST/PUT/PATCH/DELETE exists on /audit).
 */
export function useAuditEvents(
  params: { skip?: number; limit?: number } & AuditEventListFilters = {}
) {
  const query = {
    skip: params.skip ?? 0,
    limit: params.limit ?? 50,
    event_type: params.event_type,
    category: params.category,
    outcome: params.outcome,
    resource_type: params.resource_type,
    actor_type: params.actor_type,
    scan_id: params.scan_id,
  };
  return useQuery({
    queryKey: auditKeys.list(query),
    queryFn: () => auditApi.getAuditEvents(query),
  });
}
