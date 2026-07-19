import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/errors";
import { renderWithQueryClient } from "@/test/render";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
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

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { scansApi } from "@/features/scans/api/scans-api";
import { TargetRowActions } from "@/features/targets/components/target-row-actions";
import { toast } from "sonner";

const mockedCreateScan = vi.mocked(scansApi.createScan);

const target = {
  id: "22222222-2222-2222-2222-222222222222",
  target: "10.0.0.5",
  target_type: "IPV4" as const,
  created_at: "2026-07-15T00:00:00Z",
  updated_at: "2026-07-15T00:00:00Z",
};

async function openMenuAndStartScan() {
  const user = userEvent.setup();
  renderWithQueryClient(
    <TargetRowActions target={target} onDeleteRequest={() => {}} />
  );
  await user.click(screen.getByRole("button", { name: /actions for/i }));
  await user.click(await screen.findByText("Start Scan"));
  return user;
}

describe("StartScanMenuItem (via TargetRowActions)", () => {
  it("sends only the target_id the backend requires — no frontend-fabricated fields", async () => {
    mockedCreateScan.mockResolvedValue({
      scan_id: "33333333-3333-3333-3333-333333333333",
      target_id: target.id,
      status: "RUNNING",
      scan_type: "full",
      created_at: "2026-07-15T00:00:00Z",
      updated_at: "2026-07-15T00:00:00Z",
      started_at: "2026-07-15T00:00:00Z",
      completed_at: null,
      execution_duration: null,
      failure_reason: null,
      output_file_path: null,
      stdout_log: null,
      stderr_log: null,
    });

    await openMenuAndStartScan();

    await waitFor(() =>
      expect(mockedCreateScan).toHaveBeenCalledWith({ target_id: target.id })
    );
    expect(mockedCreateScan).toHaveBeenCalledTimes(1);
    await waitFor(() =>
      expect(push).toHaveBeenCalledWith("/scans/33333333-3333-3333-3333-333333333333")
    );
  });

  it("surfaces a 409 (already-running) conflict as a safe toast and never retries automatically", async () => {
    mockedCreateScan.mockRejectedValue(
      new ApiError({
        code: "CONFLICT",
        message: `A scan is already running for target ${target.id}.`,
        status: 409,
      })
    );

    await openMenuAndStartScan();

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith(
        `A scan is already running for target ${target.id}.`
      )
    );
    expect(mockedCreateScan).toHaveBeenCalledTimes(1);
    expect(push).not.toHaveBeenCalled();
  });
});
