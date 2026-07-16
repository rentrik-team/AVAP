import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "@/test/render";

vi.mock("@/features/assets/api/assets-api", () => ({
  assetsApi: {
    getAssets: vi.fn(),
    getAsset: vi.fn(),
    deleteAsset: vi.fn(),
  },
}));

import { assetsApi } from "@/features/assets/api/assets-api";
import { AssetList } from "@/features/assets/components/asset-list";

const mockedGetAssets = vi.mocked(assetsApi.getAssets);

function sampleAsset(overrides: Partial<Parameters<typeof Object.assign>[0]> = {}) {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    ipv4: "10.0.0.5",
    hostname: "web.local",
    operating_system: "Linux",
    created_at: "2026-07-15T00:00:00Z",
    updated_at: "2026-07-15T00:00:00Z",
    ...overrides,
  };
}

describe("AssetList — states", () => {
  it("shows the true-empty state (no filters active) without a fabricated create action", async () => {
    mockedGetAssets.mockResolvedValue({ assets: [], total: 0 });

    renderWithQueryClient(<AssetList />);

    await waitFor(() =>
      expect(screen.getByText("No assets have been discovered yet")).toBeInTheDocument()
    );
    expect(screen.queryByRole("button", { name: /create asset/i })).not.toBeInTheDocument();
  });

  it("shows the sanitized error state — not an empty inventory — on failure", async () => {
    mockedGetAssets.mockRejectedValue(new Error("network down"));

    renderWithQueryClient(<AssetList />);

    await waitFor(() =>
      expect(screen.getByText("Unable to load assets")).toBeInTheDocument()
    );
    expect(screen.queryByText("No assets have been discovered yet")).not.toBeInTheDocument();
  });

  it("shows a distinct filtered-empty state with a working Clear filters action", async () => {
    mockedGetAssets.mockResolvedValue({ assets: [], total: 0 });

    const user = userEvent.setup();
    renderWithQueryClient(<AssetList />);
    await user.type(screen.getByLabelText("IP address"), "10.0.0.99");

    await waitFor(
      () => expect(screen.getByText("No assets match these filters")).toBeInTheDocument(),
      { timeout: 2000 }
    );

    await user.click(screen.getByRole("button", { name: /clear filters/i }));
    await waitFor(() =>
      expect(screen.getByText("No assets have been discovered yet")).toBeInTheDocument()
    );
  });

  it("renders discovered assets with technical fields", async () => {
    mockedGetAssets.mockResolvedValue({ assets: [sampleAsset()], total: 1 });

    renderWithQueryClient(<AssetList />);

    await waitFor(() => expect(screen.getAllByText("10.0.0.5")[0]).toBeInTheDocument());
    expect(screen.getAllByText("web.local")[0]).toBeInTheDocument();
  });
});

describe("AssetList — server-side filtering", () => {
  it("maps the IP filter to an exact backend query param", async () => {
    mockedGetAssets.mockResolvedValue({ assets: [], total: 0 });
    const user = userEvent.setup();
    renderWithQueryClient(<AssetList />);

    await user.type(screen.getByLabelText("IP address"), "10.0.0.5");

    await waitFor(
      () =>
        expect(mockedGetAssets).toHaveBeenLastCalledWith(
          expect.objectContaining({ ip: "10.0.0.5", hostname: undefined, port: undefined, cve: undefined })
        ),
      { timeout: 2000 }
    );
  });

  it("maps the hostname filter", async () => {
    mockedGetAssets.mockResolvedValue({ assets: [], total: 0 });
    const user = userEvent.setup();
    renderWithQueryClient(<AssetList />);

    await user.type(screen.getByLabelText("Hostname"), "web-server");

    await waitFor(
      () =>
        expect(mockedGetAssets).toHaveBeenLastCalledWith(
          expect.objectContaining({ hostname: "web-server" })
        ),
      { timeout: 2000 }
    );
  });

  it("maps a valid port filter, and never sends an unparseable port to the backend", async () => {
    mockedGetAssets.mockResolvedValue({ assets: [], total: 0 });
    const user = userEvent.setup();
    renderWithQueryClient(<AssetList />);

    await user.type(screen.getByLabelText("Port"), "abc");
    // Wait for the debounce to actually settle on "abc" (proven by the
    // inline validation message appearing) before asserting on the mock —
    // asserting on the mock alone is racy, since the initial mount call
    // also happens to have port: undefined.
    await screen.findByText("Enter a port between 1 and 65535.", {}, { timeout: 2000 });
    expect(mockedGetAssets).toHaveBeenLastCalledWith(
      expect.objectContaining({ port: undefined })
    );

    await user.clear(screen.getByLabelText("Port"));
    await user.type(screen.getByLabelText("Port"), "8443");
    await waitFor(
      () =>
        expect(mockedGetAssets).toHaveBeenLastCalledWith(
          expect.objectContaining({ port: 8443 })
        ),
      { timeout: 2000 }
    );
  });

  it("maps the CVE filter", async () => {
    mockedGetAssets.mockResolvedValue({ assets: [], total: 0 });
    const user = userEvent.setup();
    renderWithQueryClient(<AssetList />);

    await user.type(screen.getByLabelText("CVE"), "CVE-2024-12345");

    await waitFor(
      () =>
        expect(mockedGetAssets).toHaveBeenLastCalledWith(
          expect.objectContaining({ cve: "CVE-2024-12345" })
        ),
      { timeout: 2000 }
    );
  });

  it("resets to the first page when the active filter set changes", async () => {
    mockedGetAssets.mockResolvedValue({
      assets: Array.from({ length: 1 }, () => sampleAsset()),
      total: 120,
    });
    const user = userEvent.setup();
    renderWithQueryClient(<AssetList />);

    await waitFor(() => expect(screen.getByRole("button", { name: /next/i })).toBeEnabled());
    await user.click(screen.getByRole("button", { name: /next/i }));
    await waitFor(() =>
      expect(mockedGetAssets).toHaveBeenLastCalledWith(expect.objectContaining({ skip: 50 }))
    );

    await user.type(screen.getByLabelText("Hostname"), "db");
    await waitFor(
      () =>
        expect(mockedGetAssets).toHaveBeenLastCalledWith(
          expect.objectContaining({ skip: 0, hostname: "db" })
        ),
      { timeout: 2000 }
    );
  });
});
