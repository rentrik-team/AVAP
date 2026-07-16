import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/features/risk/api/risk-api", () => ({
  riskApi: {
    getRiskAssessments: vi.fn(),
    getRiskByScan: vi.fn(),
    calculateRiskForScan: vi.fn(),
    getRiskSummary: vi.fn(),
  },
}));

import { riskApi } from "@/features/risk/api/risk-api";
import { useCalculateRiskForScan } from "@/features/risk/hooks/use-risk";

const mockedCalculate = vi.mocked(riskApi.calculateRiskForScan);

function wrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe("useCalculateRiskForScan — cache invalidation map", () => {
  it("invalidates exactly risk lists/summary/scan and dashboard summary/risk/ai — never dashboard scans/reports or the AI feature's own cache", async () => {
    mockedCalculate.mockResolvedValue({
      id: "risk-1",
      scope: "SCAN",
      risk_score: 7.2,
      risk_level: "HIGH",
      calculation_version: "1.0.0",
      calculated_at: "2026-07-15T00:00:00Z",
      supporting_factors: {},
      scan_id: "scan-1",
      asset_id: null,
      vulnerability_id: null,
      service_id: null,
    });

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useCalculateRiskForScan(), {
      wrapper: wrapper(queryClient),
    });

    result.current.mutate("scan-1");
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const invalidatedKeys = invalidateSpy.mock.calls.map((call) => call[0]?.queryKey);

    expect(invalidatedKeys).toContainEqual(["risk", "list"]);
    expect(invalidatedKeys).toContainEqual(["risk", "summary"]);
    expect(invalidatedKeys).toContainEqual(["dashboard", "summary"]);
    expect(invalidatedKeys).toContainEqual(["dashboard", "risk"]);
    expect(invalidatedKeys).toContainEqual(["dashboard", "ai"]);

    // Never broadly invalidated: dashboard/scans and dashboard/reports have
    // no FK path from risk_assessments (verified against dashboard_service.py).
    expect(invalidatedKeys).not.toContainEqual(["dashboard", "scans"]);
    expect(invalidatedKeys).not.toContainEqual(["dashboard", "reports"]);
    // The AI feature's own recommendation cache is never touched by risk
    // calculation — no AIRecommendation row is written by this mutation.
    expect(invalidatedKeys.some((key) => Array.isArray(key) && key[0] === "ai")).toBe(false);

    // scan-specific risk is applied via setQueryData (authoritative
    // response), not invalidation — confirm the cache actually holds it.
    expect(queryClient.getQueryData(["risk", "scan", "scan-1"])).toMatchObject({
      risk_score: 7.2,
    });
  });
});
