import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/errors";
import { renderWithQueryClient } from "@/test/render";

vi.mock("@/features/assets/api/assets-api", () => ({
  assetsApi: {
    getAssets: vi.fn(),
    getAsset: vi.fn(),
    deleteAsset: vi.fn(),
  },
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { assetsApi } from "@/features/assets/api/assets-api";
import { DeleteAssetDialog } from "@/features/assets/components/delete-asset-dialog";
import { toast } from "sonner";

const mockedDeleteAsset = vi.mocked(assetsApi.deleteAsset);

const asset = {
  id: "11111111-1111-1111-1111-111111111111",
  ipv4: "10.0.0.5",
  hostname: "web.local",
  operating_system: "Linux",
  created_at: "2026-07-15T00:00:00Z",
  updated_at: "2026-07-15T00:00:00Z",
};

describe("DeleteAssetDialog", () => {
  it("identifies the exact asset and discloses accurate (not overclaimed) cascade behavior", () => {
    renderWithQueryClient(
      <DeleteAssetDialog asset={asset} open onOpenChange={() => {}} />
    );
    expect(screen.getByText("10.0.0.5")).toBeInTheDocument();
    expect(screen.getByText("web.local")).toBeInTheDocument();
    // Must not claim vulnerability catalog identities or reports are deleted.
    const description = screen.getByText(/permanently removes the asset/i);
    expect(description.textContent).toMatch(/not affected/i);
  });

  it("waits for server confirmation before closing — no optimistic removal", async () => {
    let resolveDelete: () => void = () => {};
    mockedDeleteAsset.mockImplementation(
      () => new Promise((resolve) => { resolveDelete = () => resolve(undefined); })
    );
    const onOpenChange = vi.fn();
    const user = userEvent.setup();

    renderWithQueryClient(
      <DeleteAssetDialog asset={asset} open onOpenChange={onOpenChange} />
    );
    await user.click(screen.getByRole("button", { name: /delete asset/i }));

    expect(mockedDeleteAsset).toHaveBeenCalledWith(asset.id);
    expect(onOpenChange).not.toHaveBeenCalled();

    resolveDelete();
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
    expect(toast.success).toHaveBeenCalledWith("Asset deleted");
  });

  it("preserves the dialog and surfaces a safe message on failure — no raw error leaked", async () => {
    mockedDeleteAsset.mockRejectedValue(
      new ApiError({ code: "NOT_FOUND", message: "Asset with ID 1 not found.", status: 404 })
    );
    const onOpenChange = vi.fn();
    const user = userEvent.setup();

    renderWithQueryClient(
      <DeleteAssetDialog asset={asset} open onOpenChange={onOpenChange} />
    );
    await user.click(screen.getByRole("button", { name: /delete asset/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith("Asset with ID 1 not found.")
    );
    expect(onOpenChange).not.toHaveBeenCalledWith(false);
  });
});
