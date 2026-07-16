import type { RiskListFilters } from "@/features/risk/types/risk";

/** Deterministic query key factory for the Risk feature. */
export const riskKeys = {
  all: ["risk"] as const,
  lists: () => [...riskKeys.all, "list"] as const,
  list: (params: { skip: number; limit: number } & RiskListFilters) =>
    [...riskKeys.lists(), params] as const,
  summary: () => [...riskKeys.all, "summary"] as const,
  scans: () => [...riskKeys.all, "scan"] as const,
  scan: (scanId: string) => [...riskKeys.scans(), scanId] as const,
};
