import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TooltipProvider } from "@/components/ui/tooltip";
import { ScanRowActions } from "@/features/scans/components/scan-row-actions";
import type { ScanResponse } from "@/features/scans/types/scan";

function scan(overrides: Partial<ScanResponse> = {}): ScanResponse {
  return {
    scan_id: "33333333-3333-3333-3333-333333333333",
    target_id: "22222222-2222-2222-2222-222222222222",
    status: "COMPLETED",
    scan_type: "full",
    created_at: "2026-07-15T00:00:00Z",
    updated_at: "2026-07-15T00:00:00Z",
    started_at: "2026-07-15T00:00:00Z",
    completed_at: "2026-07-15T00:05:00Z",
    execution_duration: 300,
    failure_reason: null,
    stdout_log: null,
    stderr_log: null,
    ...overrides,
  };
}

describe("ScanRowActions", () => {
  it("disables Delete for a RUNNING scan, matching the backend's protection rule proactively", async () => {
    const user = userEvent.setup();
    render(
      <TooltipProvider>
        <ScanRowActions scan={scan({ status: "RUNNING" })} onDeleteRequest={vi.fn()} />
      </TooltipProvider>
    );

    await user.click(screen.getByRole("button", { name: /scan actions/i }));
    expect(await screen.findByText("Delete")).toHaveAttribute("data-disabled");
  });

  it("allows requesting deletion for a terminal-state scan", async () => {
    const onDeleteRequest = vi.fn();
    const user = userEvent.setup();
    render(<ScanRowActions scan={scan()} onDeleteRequest={onDeleteRequest} />);

    await user.click(screen.getByRole("button", { name: /scan actions/i }));
    await user.click(await screen.findByText("Delete"));

    expect(onDeleteRequest).toHaveBeenCalledWith(scan());
  });
});
