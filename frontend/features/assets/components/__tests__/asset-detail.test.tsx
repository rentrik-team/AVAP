import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "@/test/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/features/assets/api/assets-api", () => ({
  assetsApi: {
    getAssets: vi.fn(),
    getAsset: vi.fn(),
    deleteAsset: vi.fn(),
  },
}));

import { assetsApi } from "@/features/assets/api/assets-api";
import { AssetDetail } from "@/features/assets/components/asset-detail";

const mockedGetAsset = vi.mocked(assetsApi.getAsset);

describe("AssetDetail", () => {
  it("renders nested services as inert technical text, never a clickable connectivity action", async () => {
    mockedGetAsset.mockResolvedValue({
      id: "11111111-1111-1111-1111-111111111111",
      ipv4: "10.0.0.5",
      hostname: "web.local",
      operating_system: "Ubuntu 24.04",
      created_at: "2026-07-15T00:00:00Z",
      updated_at: "2026-07-15T00:00:00Z",
      services: [
        {
          id: "s1",
          port: 443,
          protocol: "tcp",
          service_name: "https",
          product: "nginx",
          version: "1.24",
          extra_info: null,
          created_at: "2026-07-15T00:00:00Z",
          updated_at: "2026-07-15T00:00:00Z",
        },
      ],
    });

    renderWithQueryClient(<AssetDetail assetId="11111111-1111-1111-1111-111111111111" />);

    expect(await screen.findByText("443/TCP")).toBeInTheDocument();
    expect(screen.getByText("https")).toBeInTheDocument();
    expect(screen.getByText("nginx 1.24")).toBeInTheDocument();

    // No generated URLs, no "Open"/"Visit"/"Test Connection" actions.
    expect(screen.queryByRole("link", { name: /open|visit|connect/i })).not.toBeInTheDocument();
    expect(document.querySelectorAll("a[href^='http']").length).toBe(0);
  });

  it("shows a message rather than a blank section when no services were discovered", async () => {
    mockedGetAsset.mockResolvedValue({
      id: "22222222-2222-2222-2222-222222222222",
      ipv4: "10.0.0.9",
      hostname: null,
      operating_system: null,
      created_at: "2026-07-15T00:00:00Z",
      updated_at: "2026-07-15T00:00:00Z",
      services: [],
    });

    renderWithQueryClient(<AssetDetail assetId="22222222-2222-2222-2222-222222222222" />);

    expect(
      await screen.findByText("No open services discovered for this asset.")
    ).toBeInTheDocument();
  });

  it("shows the sanitized error state on a not-found/failed fetch", async () => {
    mockedGetAsset.mockRejectedValue(new Error("boom"));

    renderWithQueryClient(<AssetDetail assetId="does-not-exist" />);

    await waitFor(() =>
      expect(screen.getByText("Unable to load this asset")).toBeInTheDocument()
    );
  });
});
