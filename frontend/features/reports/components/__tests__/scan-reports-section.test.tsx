import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/errors";
import { renderWithQueryClient } from "@/test/render";

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
import { ScanReportsSection } from "@/features/reports/components/scan-reports-section";
import { toast } from "sonner";

const mockedGetReports = vi.mocked(reportsApi.getReports);
const mockedGenerateReport = vi.mocked(reportsApi.generateReport);

describe("ScanReportsSection", () => {
  it("does not offer Generate Report for a non-completed scan", async () => {
    mockedGetReports.mockResolvedValue({ reports: [], total: 0 });
    renderWithQueryClient(<ScanReportsSection scanId="scan-1" scanStatus="RUNNING" />);

    await waitFor(() =>
      expect(
        screen.getByText(/reports can be generated once this scan completes/i)
      ).toBeInTheDocument()
    );
    expect(
      screen.queryByRole("button", { name: /generate report/i })
    ).not.toBeInTheDocument();
  });

  it("offers Generate Report for a completed scan and calls the exact scan_id", async () => {
    mockedGetReports.mockResolvedValue({ reports: [], total: 0 });
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

    const user = userEvent.setup();
    renderWithQueryClient(<ScanReportsSection scanId="scan-1" scanStatus="COMPLETED" />);

    await user.click(await screen.findByRole("button", { name: /generate report/i }));

    await waitFor(() => expect(mockedGenerateReport).toHaveBeenCalledWith("scan-1"));
    await waitFor(() => expect(toast.success).toHaveBeenCalledWith("Report generated"));
  });

  it("surfaces a 422 (risk not yet calculated) failure safely, without blaming AI", async () => {
    mockedGetReports.mockResolvedValue({ reports: [], total: 0 });
    mockedGenerateReport.mockRejectedValue(
      new ApiError({
        code: "INSUFFICIENT_REPORT_DATA",
        message: "No deterministic risk assessment is available for scan scan-1.",
        status: 422,
      })
    );

    const user = userEvent.setup();
    renderWithQueryClient(<ScanReportsSection scanId="scan-1" scanStatus="COMPLETED" />);

    await user.click(await screen.findByRole("button", { name: /generate report/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith(
        "No deterministic risk assessment is available for scan scan-1."
      )
    );
  });

  it("lists existing reports for this scan using the same server-side scan_id filter as the main Reports page", async () => {
    mockedGetReports.mockResolvedValue({
      reports: [
        {
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
        },
      ],
      total: 1,
    });

    renderWithQueryClient(<ScanReportsSection scanId="scan-1" scanStatus="COMPLETED" />);

    await screen.findByText("PDF Report");
    expect(mockedGetReports).toHaveBeenCalledWith(
      expect.objectContaining({ scan_id: "scan-1" })
    );
  });
});
