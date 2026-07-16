import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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

import { reportsApi } from "@/features/reports/api/reports-api";
import { ReportList } from "@/features/reports/components/report-list";

const mockedGetReports = vi.mocked(reportsApi.getReports);

function sampleReport() {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    scan_id: "22222222-2222-2222-2222-222222222222",
    format: "PDF",
    report_template_version: "1.0.0",
    risk_calculation_version: "1.0.0",
    overall_risk_score: 8.7,
    overall_risk_level: "CRITICAL" as const,
    vulnerability_count: 5,
    ai_recommendations_included: 3,
    file_size_bytes: 245_000,
    generated_at: "2026-07-15T00:00:00Z",
  };
}

describe("ReportList", () => {
  it("shows the true-empty state, no fabricated report data", async () => {
    mockedGetReports.mockResolvedValue({ reports: [], total: 0 });
    renderWithQueryClient(<ReportList />);

    await waitFor(() =>
      expect(
        screen.getByText("No reports have been generated yet")
      ).toBeInTheDocument()
    );
  });

  it("shows the sanitized error state on failure", async () => {
    mockedGetReports.mockRejectedValue(new Error("network down"));
    renderWithQueryClient(<ReportList />);

    await waitFor(() =>
      expect(screen.getByText("Unable to load reports")).toBeInTheDocument()
    );
  });

  it("renders report rows via RiskScore/RiskLevelBadge and never exposes a filesystem path", async () => {
    mockedGetReports.mockResolvedValue({ reports: [sampleReport()], total: 1 });
    renderWithQueryClient(<ReportList />);

    await waitFor(() => expect(screen.getAllByText("8.7")[0]).toBeInTheDocument());
    expect(screen.getAllByText("Critical")[0]).toBeInTheDocument();

    // Never a server-generated internal file name or storage path.
    expect(document.body.textContent).not.toMatch(/report_[0-9a-f-]+\.pdf/i);
    expect(document.body.textContent).not.toMatch(/REPORT_OUTPUT_DIRECTORY|storage_root|\/var\/|C:\\/i);
  });

  it("does not render a manual scan_id filter input (documented UX decision)", async () => {
    mockedGetReports.mockResolvedValue({ reports: [sampleReport()], total: 1 });
    renderWithQueryClient(<ReportList />);

    await screen.findAllByText("8.7");
    expect(screen.queryByLabelText(/scan.*id/i)).not.toBeInTheDocument();
  });

  it("uses server-side pagination derived from the backend total, never fabricated", async () => {
    mockedGetReports.mockResolvedValue({ reports: [sampleReport()], total: 120 });
    renderWithQueryClient(<ReportList />);

    await waitFor(() => expect(screen.getByRole("button", { name: /next/i })).toBeEnabled());
    expect(screen.getByText(/of 120/)).toBeInTheDocument();
  });
});
