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

vi.mock("@/features/risk/api/risk-api", () => ({
  riskApi: {
    getRiskByScan: vi.fn(),
  },
}));

import { reportsApi } from "@/features/reports/api/reports-api";
import { ScanReportsSection } from "@/features/reports/components/scan-reports-section";
import { riskApi } from "@/features/risk/api/risk-api";
import type { RiskAssessmentResponse } from "@/features/risk/types/risk";
import { toast } from "sonner";

const mockedGetReports = vi.mocked(reportsApi.getReports);
const mockedGenerateReport = vi.mocked(reportsApi.generateReport);
const mockedGetRiskByScan = vi.mocked(riskApi.getRiskByScan);

const sampleScanRisk: RiskAssessmentResponse = {
  id: "risk-1",
  scope: "SCAN",
  risk_score: 7.0,
  risk_level: "HIGH",
  calculation_version: "1.0.0",
  calculated_at: "2026-07-15T00:00:00Z",
  supporting_factors: {},
  scan_id: "scan-1",
  asset_id: null,
  vulnerability_id: null,
  service_id: null,
};

/** Backend answers 404 for a scan whose risk was never calculated. */
function mockRiskNotCalculated() {
  mockedGetRiskByScan.mockRejectedValue(
    new ApiError({
      code: "NOT_FOUND",
      message: "No risk assessment found for scan scan-1.",
      status: 404,
    })
  );
}

describe("ScanReportsSection", () => {
  it("does not offer Generate Report for a non-completed scan", async () => {
    mockedGetReports.mockResolvedValue({ reports: [], total: 0 });
    mockRiskNotCalculated();
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

  it("disables Generate Report on a completed scan until risk is calculated, and says why", async () => {
    mockedGetReports.mockResolvedValue({ reports: [], total: 0 });
    mockRiskNotCalculated();

    renderWithQueryClient(<ScanReportsSection scanId="scan-1" scanStatus="COMPLETED" />);

    const button = await screen.findByRole("button", { name: /generate report/i });
    await waitFor(() => expect(button).toBeDisabled());
    expect(
      screen.getByText(/calculate risk above to enable report generation/i)
    ).toBeInTheDocument();
  });

  it("offers Generate Report for a completed scan with calculated risk and calls the exact scan_id", async () => {
    mockedGetReports.mockResolvedValue({ reports: [], total: 0 });
    mockedGetRiskByScan.mockResolvedValue(sampleScanRisk);
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

    const button = await screen.findByRole("button", { name: /generate report/i });
    await waitFor(() => expect(button).toBeEnabled());
    await user.click(button);

    await waitFor(() => expect(mockedGenerateReport).toHaveBeenCalledWith("scan-1"));
    await waitFor(() => expect(toast.success).toHaveBeenCalledWith("Report generated"));
  });

  it("surfaces a 422 (risk not yet calculated) failure safely, without blaming AI", async () => {
    mockedGetReports.mockResolvedValue({ reports: [], total: 0 });
    mockedGetRiskByScan.mockResolvedValue(sampleScanRisk);
    mockedGenerateReport.mockRejectedValue(
      new ApiError({
        code: "INSUFFICIENT_REPORT_DATA",
        message: "No deterministic risk assessment is available for scan scan-1.",
        status: 422,
      })
    );

    const user = userEvent.setup();
    renderWithQueryClient(<ScanReportsSection scanId="scan-1" scanStatus="COMPLETED" />);

    const button = await screen.findByRole("button", { name: /generate report/i });
    await waitFor(() => expect(button).toBeEnabled());
    await user.click(button);

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith(
        "No deterministic risk assessment is available for scan scan-1."
      )
    );
  });

  it("lists existing reports for this scan using the same server-side scan_id filter as the main Reports page", async () => {
    mockedGetRiskByScan.mockResolvedValue(sampleScanRisk);
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
