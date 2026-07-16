import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/features/reports/api/reports-api", () => ({
  reportsApi: {
    getReports: vi.fn(),
    getReport: vi.fn(),
    generateReport: vi.fn(),
    deleteReport: vi.fn(),
    downloadReport: vi.fn(),
  },
}));

import { reportsApi } from "@/features/reports/api/reports-api";
import { useGenerateReport } from "@/features/reports/hooks/use-reports";

const mockedGenerateReport = vi.mocked(reportsApi.generateReport);

function wrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe("useGenerateReport — cache invalidation map", () => {
  it("invalidates only reports/dashboard-summary/dashboard-reports — never risk, AI, assets, vulnerabilities, or scans", async () => {
    mockedGenerateReport.mockResolvedValue({
      id: "report-1",
      scan_id: "scan-1",
      format: "PDF",
      report_template_version: "1.0.0",
      risk_calculation_version: "1.0.0",
      overall_risk_score: 7.0,
      overall_risk_level: "HIGH",
      vulnerability_count: 2,
      ai_recommendations_included: 1,
      file_size_bytes: 1000,
      generated_at: "2026-07-15T00:00:00Z",
    });

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useGenerateReport(), {
      wrapper: wrapper(queryClient),
    });

    result.current.mutate("scan-1");
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const invalidatedKeys = invalidateSpy.mock.calls.map((call) => call[0]?.queryKey);

    expect(invalidatedKeys).toContainEqual(["reports", "list"]);
    expect(invalidatedKeys).toContainEqual(["dashboard", "summary"]);
    expect(invalidatedKeys).toContainEqual(["dashboard", "reports"]);

    expect(invalidatedKeys.some((key) => Array.isArray(key) && key[0] === "risk")).toBe(false);
    expect(invalidatedKeys.some((key) => Array.isArray(key) && key[0] === "ai")).toBe(false);
    expect(invalidatedKeys).not.toContainEqual(["dashboard", "assets"]);
    expect(invalidatedKeys).not.toContainEqual(["dashboard", "vulnerabilities"]);
    expect(invalidatedKeys).not.toContainEqual(["dashboard", "scans"]);
  });
});
