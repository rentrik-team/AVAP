import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/errors";
import { renderWithQueryClient } from "@/test/render";

vi.mock("@/features/targets/api/targets-api", () => ({
  targetsApi: {
    getTargets: vi.fn(),
    getTarget: vi.fn(),
    createTarget: vi.fn(),
    deleteTarget: vi.fn(),
  },
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { targetsApi } from "@/features/targets/api/targets-api";
import { DeleteTargetDialog } from "@/features/targets/components/delete-target-dialog";
import { toast } from "sonner";

const mockedDeleteTarget = vi.mocked(targetsApi.deleteTarget);

const target = {
  id: "11111111-1111-1111-1111-111111111111",
  target: "10.0.0.5",
  target_type: "IPV4" as const,
  created_at: "2026-07-15T00:00:00Z",
  updated_at: "2026-07-15T00:00:00Z",
};

describe("DeleteTargetDialog", () => {
  it("clearly identifies the exact target being deleted", () => {
    renderWithQueryClient(
      <DeleteTargetDialog target={target} open onOpenChange={() => {}} />
    );
    expect(screen.getByText("10.0.0.5")).toBeInTheDocument();
  });

  it("waits for server confirmation before closing — does not remove optimistically", async () => {
    let resolveDelete: () => void = () => {};
    mockedDeleteTarget.mockImplementation(
      () => new Promise((resolve) => { resolveDelete = () => resolve(undefined); })
    );
    const onOpenChange = vi.fn();
    const user = userEvent.setup();

    renderWithQueryClient(
      <DeleteTargetDialog target={target} open onOpenChange={onOpenChange} />
    );
    await user.click(screen.getByRole("button", { name: /delete target/i }));

    expect(mockedDeleteTarget).toHaveBeenCalledWith(target.id);
    expect(onOpenChange).not.toHaveBeenCalled();

    resolveDelete();
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
    expect(toast.success).toHaveBeenCalledWith("Target deleted");
  });

  it("surfaces a delete failure safely and keeps the dialog open for a genuine retry", async () => {
    mockedDeleteTarget.mockRejectedValue(
      new ApiError({ code: "UNKNOWN_ERROR", message: "An unexpected error occurred. Please try again.", status: null })
    );
    const onOpenChange = vi.fn();
    const user = userEvent.setup();

    renderWithQueryClient(
      <DeleteTargetDialog target={target} open onOpenChange={onOpenChange} />
    );
    await user.click(screen.getByRole("button", { name: /delete target/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith(
        "An unexpected error occurred. Please try again."
      )
    );
    expect(onOpenChange).not.toHaveBeenCalledWith(false);
  });
});
