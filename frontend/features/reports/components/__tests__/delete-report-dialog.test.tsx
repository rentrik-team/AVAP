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
import { DeleteReportDialog } from "@/features/reports/components/delete-report-dialog";
import { toast } from "sonner";

const mockedDeleteReport = vi.mocked(reportsApi.deleteReport);

const report = {
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

describe("DeleteReportDialog", () => {
  it("discloses accurate (not overclaimed) deletion scope", () => {
    renderWithQueryClient(
      <DeleteReportDialog report={report} open onOpenChange={() => {}} />
    );
    const description = screen.getByText(/permanently removes the report metadata/i);
    expect(description.textContent).toMatch(/not affected/i);
  });

  it("waits for server confirmation before closing — no optimistic removal", async () => {
    let resolveDelete: (value: undefined) => void = () => {};
    mockedDeleteReport.mockImplementation(
      () => new Promise((resolve) => { resolveDelete = resolve; })
    );
    const onOpenChange = vi.fn();
    const user = userEvent.setup();

    renderWithQueryClient(
      <DeleteReportDialog report={report} open onOpenChange={onOpenChange} />
    );
    await user.click(screen.getByRole("button", { name: /delete report/i }));

    expect(mockedDeleteReport).toHaveBeenCalledWith(report.id);
    expect(onOpenChange).not.toHaveBeenCalled();

    resolveDelete(undefined);
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
    expect(toast.success).toHaveBeenCalledWith("Report deleted");
  });

  it("surfaces a delete failure safely without a raw error leaking", async () => {
    mockedDeleteReport.mockRejectedValue(
      new ApiError({ code: "NOT_FOUND", message: "Report 1 not found.", status: 404 })
    );
    const onOpenChange = vi.fn();
    const user = userEvent.setup();

    renderWithQueryClient(
      <DeleteReportDialog report={report} open onOpenChange={onOpenChange} />
    );
    await user.click(screen.getByRole("button", { name: /delete report/i }));

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Report 1 not found."));
    expect(onOpenChange).not.toHaveBeenCalledWith(false);
  });
});
