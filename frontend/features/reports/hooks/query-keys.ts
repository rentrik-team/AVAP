import type { ReportListFilters } from "@/features/reports/types/report";

/** Deterministic query key factory for the Reports feature. */
export const reportKeys = {
  all: ["reports"] as const,
  lists: () => [...reportKeys.all, "list"] as const,
  list: (params: { skip: number; limit: number } & ReportListFilters) =>
    [...reportKeys.lists(), params] as const,
  details: () => [...reportKeys.all, "detail"] as const,
  detail: (id: string) => [...reportKeys.details(), id] as const,
};
