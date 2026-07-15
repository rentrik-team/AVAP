import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "@/test/render";

vi.mock("@/features/dashboard/api/dashboard-api", () => ({
  dashboardApi: {
    getScanStatistics: vi.fn(),
  },
}));

import { dashboardApi } from "@/features/dashboard/api/dashboard-api";
import { ScanActivity } from "@/features/dashboard/components/scan-activity";

const mockedGetScanStatistics = vi.mocked(dashboardApi.getScanStatistics);

describe("ScanActivity", () => {
  it("renders a premium empty state on an empty platform, not a blank screen", async () => {
    mockedGetScanStatistics.mockResolvedValue({
      generated_at: "2026-07-15T00:00:00Z",
      total_scans: 0,
      scans_by_status: { pending: 0, running: 0, completed: 0, failed: 0 },
      scan_success_rate_percent: 0,
      average_scan_duration_seconds: null,
      recent_scans: [],
    });

    renderWithQueryClient(<ScanActivity />);

    await waitFor(() => expect(screen.getByText("No scans yet")).toBeInTheDocument());
    expect(screen.getByText("0.0%")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument(); // avg duration, no fabricated value
  });

  it("never renders a fabricated progress percentage for a RUNNING scan (backend only exposes status)", async () => {
    mockedGetScanStatistics.mockResolvedValue({
      generated_at: "2026-07-15T00:00:00Z",
      total_scans: 1,
      scans_by_status: { pending: 0, running: 1, completed: 0, failed: 0 },
      scan_success_rate_percent: 0,
      average_scan_duration_seconds: null,
      recent_scans: [
        {
          scan_id: "11111111-1111-1111-1111-111111111111",
          target: "10.0.0.5",
          target_type: "IPV4",
          status: "RUNNING",
          started_at: "2026-07-15T00:00:00Z",
          completed_at: null,
          execution_duration_seconds: null,
        },
      ],
    });

    renderWithQueryClient(<ScanActivity />);

    const statusBadge = await screen.findByText("Running");
    // Scope to the scan's own row — the sibling success-rate stat
    // legitimately renders a "%", but this specific scan's row must not
    // fabricate a progress percentage the backend never provided.
    const scanRow = statusBadge.closest("li");
    expect(scanRow).not.toBeNull();
    expect(scanRow!.textContent).not.toMatch(/\d+%/);
  });
});
