import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "@/test/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

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
import { ScanDetail } from "@/features/scans/components/scan-detail";
import { targetsApi } from "@/features/targets/api/targets-api";

const mockedGetScan = vi.mocked(scansApi.getScan);
const mockedGetScanStatus = vi.mocked(scansApi.getScanStatus);
const mockedGetTarget = vi.mocked(targetsApi.getTarget);

describe("ScanDetail", () => {
  it("never renders a fabricated progress percentage for a RUNNING scan — only the persisted status", async () => {
    mockedGetScan.mockResolvedValue({
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
      stdout_log: null,
      stderr_log: null,
    });
    mockedGetScanStatus.mockResolvedValue({
      scan_id: "33333333-3333-3333-3333-333333333333",
      status: "RUNNING",
      updated_at: "2026-07-15T00:00:00Z",
    });
    mockedGetTarget.mockResolvedValue({
      id: "22222222-2222-2222-2222-222222222222",
      target: "10.0.0.5",
      target_type: "IPV4",
      created_at: "2026-07-15T00:00:00Z",
      updated_at: "2026-07-15T00:00:00Z",
    });

    renderWithQueryClient(<ScanDetail scanId="33333333-3333-3333-3333-333333333333" />);

    await waitFor(() => expect(screen.getByText("Running")).toBeInTheDocument());
    expect(document.body.textContent).not.toMatch(/\d+%\s*complete/i);
    expect(document.body.textContent).not.toMatch(/\d+\s*of\s*\d+\s*stages/i);
    // Delete is disabled while RUNNING, matching the backend's protection rule.
    expect(screen.getByRole("button", { name: /delete/i })).toBeDisabled();
  });

  it("renders a FAILED scan's failure_reason as plain safe text", async () => {
    mockedGetScan.mockResolvedValue({
      scan_id: "44444444-4444-4444-4444-444444444444",
      target_id: "22222222-2222-2222-2222-222222222222",
      status: "FAILED",
      scan_type: "full",
      created_at: "2026-07-15T00:00:00Z",
      updated_at: "2026-07-15T00:00:00Z",
      started_at: "2026-07-15T00:00:00Z",
      completed_at: "2026-07-15T00:01:00Z",
      execution_duration: 60,
      failure_reason: "Scanner execution timed out.",
      stdout_log: null,
      stderr_log: null,
    });
    mockedGetScanStatus.mockResolvedValue({
      scan_id: "44444444-4444-4444-4444-444444444444",
      status: "FAILED",
      updated_at: "2026-07-15T00:01:00Z",
    });
    mockedGetTarget.mockResolvedValue({
      id: "22222222-2222-2222-2222-222222222222",
      target: "10.0.0.5",
      target_type: "IPV4",
      created_at: "2026-07-15T00:00:00Z",
      updated_at: "2026-07-15T00:00:00Z",
    });

    renderWithQueryClient(<ScanDetail scanId="44444444-4444-4444-4444-444444444444" />);

    expect(await screen.findByText("Scanner execution timed out.")).toBeInTheDocument();
    // A terminal (non-RUNNING) scan can be deleted.
    expect(screen.getByRole("button", { name: /delete/i })).toBeEnabled();
  });

  it("renders the full scan workflow sections, with raw output collapsed until expanded", async () => {
    mockedGetScan.mockResolvedValue({
      scan_id: "55555555-5555-5555-5555-555555555555",
      target_id: "22222222-2222-2222-2222-222222222222",
      status: "COMPLETED",
      scan_type: "full",
      created_at: "2026-07-15T00:00:00Z",
      updated_at: "2026-07-15T00:02:00Z",
      started_at: "2026-07-15T00:00:00Z",
      completed_at: "2026-07-15T00:02:00Z",
      execution_duration: 120,
      failure_reason: null,
      stdout_log: "Nmap scan report for 10.0.0.5",
      stderr_log: null,
    });
    mockedGetScanStatus.mockResolvedValue({
      scan_id: "55555555-5555-5555-5555-555555555555",
      status: "COMPLETED",
      updated_at: "2026-07-15T00:02:00Z",
    });
    mockedGetTarget.mockResolvedValue({
      id: "22222222-2222-2222-2222-222222222222",
      target: "10.0.0.5",
      target_type: "IPV4",
      created_at: "2026-07-15T00:00:00Z",
      updated_at: "2026-07-15T00:00:00Z",
    });

    renderWithQueryClient(<ScanDetail scanId="55555555-5555-5555-5555-555555555555" />);

    // Every stage of the product workflow has a visible section.
    expect(
      await screen.findByText("Discovered Hosts & Services")
    ).toBeInTheDocument();
    expect(screen.getByText("Security Analysis")).toBeInTheDocument();
    expect(screen.getByText("Risk Assessment")).toBeInTheDocument();
    expect(screen.getByText("Findings & Remediation")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();

    // Raw scanner output is optional/expandable: hidden until toggled.
    expect(
      screen.queryByText("Nmap scan report for 10.0.0.5")
    ).not.toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: /raw scanner output/i })
    );
    expect(
      screen.getByText("Nmap scan report for 10.0.0.5")
    ).toBeInTheDocument();
  });
});
