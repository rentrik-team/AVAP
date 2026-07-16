import type { AuditEventListFilters } from "@/features/audit/types/audit";

/** Deterministic query key factory for the Audit feature. */
export const auditKeys = {
  all: ["audit"] as const,
  lists: () => [...auditKeys.all, "list"] as const,
  list: (params: { skip: number; limit: number } & AuditEventListFilters) =>
    [...auditKeys.lists(), params] as const,
};
