import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "@/test/render";

vi.mock("@/features/scans/api/scans-api", () => ({
  scansApi: {
    getScans: vi.fn(),
    getScan: vi.fn(),
    getScanStatus: vi.fn(),
    createScan: vi.fn(),
    deleteScan: vi.fn(),
  },
}));

vi.mock("@/features/targets/api/targets-api", () => ({
  targetsApi: {
    getTargets: vi.fn(),
    getTarget: vi.fn(),
    createTarget: vi.fn(),
    deleteTarget: vi.fn(),
  },
}));

import { scansApi } from "@/features/scans/api/scans-api";
import { ScanList } from "@/features/scans/components/scan-list";
import { targetsApi } from "@/features/targets/api/targets-api";

const mockedGetScans = vi.mocked(scansApi.getScans);
const mockedGetTargets = vi.mocked(targetsApi.getTargets);

describe("ScanList", () => {
  it("shows a designed empty state, not a blank table, when no scans exist", async () => {
    mockedGetScans.mockResolvedValue({ scans: [], total: 0 });
    mockedGetTargets.mockResolvedValue({ targets: [], total: 0 });

    renderWithQueryClient(<ScanList />);

    await waitFor(() => expect(screen.getByText("No scans yet")).toBeInTheDocument());
  });

  it("shows the sanitized error state when the scan list request fails", async () => {
    mockedGetScans.mockRejectedValue(new Error("network down"));
    mockedGetTargets.mockResolvedValue({ targets: [], total: 0 });

    renderWithQueryClient(<ScanList />);

    await waitFor(() =>
      expect(screen.getByText("Unable to load scans")).toBeInTheDocument()
    );
  });

  it("resolves target identity via the Targets lookup and never renders a fabricated progress percentage for a RUNNING scan", async () => {
    mockedGetTargets.mockResolvedValue({
      targets: [
        {
          id: "22222222-2222-2222-2222-222222222222",
          target: "10.0.0.5",
          target_type: "IPV4",
          created_at: "2026-07-15T00:00:00Z",
          updated_at: "2026-07-15T00:00:00Z",
        },
      ],
      total: 1,
    });
    mockedGetScans.mockResolvedValue({
      scans: [
        {
          scan_id: "33333333-3333-3333-3333-333333333333",
          target_id: "22222222-2222-2222-2222-222222222222",
          status: "RUNNING",
          scan_type: "full",
          created_at: "2026-07-15T00:00:00Z",
          updated_at: "2026-07-15T00:00:00Z",
          started_at: "2026-07-15T00:00:00Z",
          completed_at: null,
          execution_duration: null,
          failure_reason: null,
        },
      ],
      total: 1,
    });

    renderWithQueryClient(<ScanList />);

    // Both the desktop table and the mobile card list render in jsdom (CSS
    // `hidden` doesn't remove nodes from the DOM), so every scan appears
    // twice — assert on each occurrence's own row/card, not just one.
    const statusBadges = await screen.findAllByText("Running");
    expect(statusBadges.length).toBeGreaterThan(0);
    for (const badge of statusBadges) {
      const row = badge.closest("tr") ?? badge.closest("[data-slot='card']");
      expect(row).not.toBeNull();
      expect(row!.textContent).not.toMatch(/\d+%/);
    }
    // Target identity resolved from the lookup map, not the raw UUID.
    expect(screen.getAllByText("10.0.0.5").length).toBeGreaterThan(0);
  });
});
