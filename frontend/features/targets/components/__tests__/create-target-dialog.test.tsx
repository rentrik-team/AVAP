import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "@/test/render";
import { ApiError } from "@/lib/api/errors";

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
import { CreateTargetDialog } from "@/features/targets/components/create-target-dialog";
import { toast } from "sonner";

const mockedCreateTarget = vi.mocked(targetsApi.createTarget);

async function openDialogAndTypeTarget(value: string) {
  const user = userEvent.setup();
  renderWithQueryClient(<CreateTargetDialog />);

  await user.click(screen.getByRole("button", { name: /new target/i }));
  const input = await screen.findByLabelText("Target");
  await user.type(input, value);
  await user.click(screen.getByRole("button", { name: /add target/i }));

  return user;
}

describe("CreateTargetDialog", () => {
  it("submits exactly {target} to the API and confirms success without leaving the dialog open", async () => {
    mockedCreateTarget.mockResolvedValue({
      id: "11111111-1111-1111-1111-111111111111",
      target: "10.0.0.5",
      target_type: "IPV4",
      created_at: "2026-07-15T00:00:00Z",
      updated_at: "2026-07-15T00:00:00Z",
    });

    await openDialogAndTypeTarget("10.0.0.5");

    await waitFor(() =>
      expect(mockedCreateTarget).toHaveBeenCalledWith({ target: "10.0.0.5" })
    );
    await waitFor(() => expect(toast.success).toHaveBeenCalledWith("Target created"));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
    );
  });

  it("surfaces the backend's 422 validation message on the field and keeps the dialog open — never a raw exception", async () => {
    mockedCreateTarget.mockRejectedValue(
      new ApiError({
        code: "VALIDATION_ERROR",
        message: "Unsupported or invalid target format: 'not a target'.",
        status: 422,
      })
    );

    await openDialogAndTypeTarget("not a target");

    expect(
      await screen.findByText("Unsupported or invalid target format: 'not a target'.")
    ).toBeInTheDocument();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("surfaces a 409 duplicate as a field error, not a generic toast", async () => {
    mockedCreateTarget.mockRejectedValue(
      new ApiError({
        code: "CONFLICT",
        message: "Target 'duplicate.com' already exists.",
        status: 409,
      })
    );

    await openDialogAndTypeTarget("duplicate.com");

    expect(
      await screen.findByText("Target 'duplicate.com' already exists.")
    ).toBeInTheDocument();
    expect(toast.error).not.toHaveBeenCalled();
  });

  it("prevents duplicate submission: rapid double-click only fires one mutation", async () => {
    let resolveCreate: (value: {
      id: string;
      target: string;
      target_type: "IPV4";
      created_at: string;
      updated_at: string;
    }) => void = () => {};
    mockedCreateTarget.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveCreate = resolve;
        })
    );

    const user = userEvent.setup();
    renderWithQueryClient(<CreateTargetDialog />);
    await user.click(screen.getByRole("button", { name: /new target/i }));
    await user.type(await screen.findByLabelText("Target"), "10.0.0.5");

    const submitButton = screen.getByRole("button", { name: /add target/i });
    await user.click(submitButton);
    // The button becomes disabled ("Adding…") once pending — a second click
    // on the same element cannot fire a second mutation.
    await waitFor(() => expect(submitButton).toBeDisabled());
    await user.click(submitButton);

    expect(mockedCreateTarget).toHaveBeenCalledTimes(1);

    resolveCreate({
      id: "1",
      target: "10.0.0.5",
      target_type: "IPV4",
      created_at: "2026-07-15T00:00:00Z",
      updated_at: "2026-07-15T00:00:00Z",
    });
  });
});
