/** Deterministic query key factory for every /dashboard/* endpoint. */
export const dashboardKeys = {
  all: ["dashboard"] as const,
  summary: () => [...dashboardKeys.all, "summary"] as const,
  assets: (limit: number) => [...dashboardKeys.all, "assets", { limit }] as const,
  vulnerabilities: () => [...dashboardKeys.all, "vulnerabilities"] as const,
  risk: (topLimit: number) => [...dashboardKeys.all, "risk", { topLimit }] as const,
  scans: (limit: number) => [...dashboardKeys.all, "scans", { limit }] as const,
  reports: (limit: number) => [...dashboardKeys.all, "reports", { limit }] as const,
  ai: () => [...dashboardKeys.all, "ai"] as const,
};
