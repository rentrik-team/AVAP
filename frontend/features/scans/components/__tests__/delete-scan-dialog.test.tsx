import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/errors";
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

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { scansApi } from "@/features/scans/api/scans-api";
import { DeleteScanDialog } from "@/features/scans/components/delete-scan-dialog";
import { toast } from "sonner";

const mockedDeleteScan = vi.mocked(scansApi.deleteScan);

const terminalScan = {
  scan_id: "33333333-3333-3333-3333-333333333333",
  target_id: "22222222-2222-2222-2222-222222222222",
  status: "COMPLETED" as const,
  scan_type: "full",
  created_at: "2026-07-15T00:00:00Z",
  updated_at: "2026-07-15T00:00:00Z",
  started_at: "2026-07-15T00:00:00Z",
  completed_at: "2026-07-15T00:05:00Z",
  execution_duration: 300,
  failure_reason: null,
  stdout_log: null,
  stderr_log: null,
};

describe("DeleteScanDialog", () => {
  it("deletes a terminal-state scan and reports success", async () => {
    mockedDeleteScan.mockResolvedValue(undefined);
    const onOpenChange = vi.fn();
    const user = userEvent.setup();

    renderWithQueryClient(
      <DeleteScanDialog scan={terminalScan} open onOpenChange={onOpenChange} />
    );
    await user.click(screen.getByRole("button", { name: /delete scan/i }));

    await waitFor(() => expect(mockedDeleteScan).toHaveBeenCalledWith(terminalScan.scan_id));
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
    expect(toast.success).toHaveBeenCalledWith("Scan deleted");
  });

  it("surfaces the backend's RUNNING-scan 409 conflict exactly — never bypassed or hidden", async () => {
    mockedDeleteScan.mockRejectedValue(
      new ApiError({
        code: "CONFLICT",
        message: "Cannot delete a running scan.",
        status: 409,
      })
    );
    const onOpenChange = vi.fn();
    const user = userEvent.setup();

    renderWithQueryClient(
      <DeleteScanDialog scan={terminalScan} open onOpenChange={onOpenChange} />
    );
    await user.click(screen.getByRole("button", { name: /delete scan/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith("Cannot delete a running scan.")
    );
    // The dialog stays open — the failure is not silently swallowed or retried.
    expect(onOpenChange).not.toHaveBeenCalledWith(false);
    expect(mockedDeleteScan).toHaveBeenCalledTimes(1);
  });
});
