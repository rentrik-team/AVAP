import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "@/test/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/features/reports/api/reports-api", () => ({
  reportsApi: {
    getReports: vi.fn(),
    getReport: vi.fn(),
    generateReport: vi.fn(),
    deleteReport: vi.fn(),
    downloadReport: vi.fn(),
  },
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { reportsApi } from "@/features/reports/api/reports-api";
import { ReportDetail } from "@/features/reports/components/report-detail";

const mockedGetReport = vi.mocked(reportsApi.getReport);
const mockedDownloadReport = vi.mocked(reportsApi.downloadReport);

function sampleReport() {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    scan_id: "22222222-2222-2222-2222-222222222222",
    format: "PDF",
    report_template_version: "1.0.0",
    risk_calculation_version: "1.1.0",
    overall_risk_score: 8.7,
    overall_risk_level: "CRITICAL" as const,
    vulnerability_count: 5,
    ai_recommendations_included: 3,
    file_size_bytes: 245_000,
    generated_at: "2026-07-15T00:00:00Z",
  };
}

describe("ReportDetail", () => {
  it("renders full metadata with human-readable file size and no internal path", async () => {
    mockedGetReport.mockResolvedValue(sampleReport());

    renderWithQueryClient(
      <ReportDetail reportId="11111111-1111-1111-1111-111111111111" />
    );

    expect(await screen.findByText("239.3 KB")).toBeInTheDocument();
    expect(screen.getByText("1.0.0")).toBeInTheDocument();
    expect(screen.getByText("1.1.0")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/report_[0-9a-f-]+\.pdf/i);
  });

  it("triggers a download via the centralized apiClient-backed mutation, not a raw fetch", async () => {
    mockedGetReport.mockResolvedValue(sampleReport());
    mockedDownloadReport.mockResolvedValue(new Blob(["%PDF-"], { type: "application/pdf" }));
    URL.createObjectURL = vi.fn(() => "blob:mock");
    URL.revokeObjectURL = vi.fn();
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    const user = userEvent.setup();
    renderWithQueryClient(
      <ReportDetail reportId="11111111-1111-1111-1111-111111111111" />
    );

    await user.click(await screen.findByRole("button", { name: /^download$/i }));

    await waitFor(() =>
      expect(mockedDownloadReport).toHaveBeenCalledWith(
        "11111111-1111-1111-1111-111111111111"
      )
    );
    expect(clickSpy).toHaveBeenCalled();
    clickSpy.mockRestore();
  });

  it("shows the sanitized error state on a not-found/failed fetch", async () => {
    mockedGetReport.mockRejectedValue(new Error("boom"));

    renderWithQueryClient(<ReportDetail reportId="does-not-exist" />);

    await waitFor(() =>
      expect(screen.getByText("Unable to load this report")).toBeInTheDocument()
    );
  });
});
