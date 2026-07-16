import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "@/test/render";

vi.mock("@/features/targets/api/targets-api", () => ({
  targetsApi: {
    getTargets: vi.fn(),
    getTarget: vi.fn(),
    createTarget: vi.fn(),
    deleteTarget: vi.fn(),
  },
}));

import { targetsApi } from "@/features/targets/api/targets-api";
import { TargetList } from "@/features/targets/components/target-list";

const mockedGetTargets = vi.mocked(targetsApi.getTargets);

describe("TargetList", () => {
  it("shows a designed empty state with a Create Target action, not a blank table", async () => {
    mockedGetTargets.mockResolvedValue({ targets: [], total: 0 });

    renderWithQueryClient(<TargetList />);

    await waitFor(() =>
      expect(screen.getByText("No targets have been added yet")).toBeInTheDocument()
    );
    expect(screen.getByRole("button", { name: /new target/i })).toBeInTheDocument();
  });

  it("shows the sanitized error state — not a silently empty table — when the request fails", async () => {
    mockedGetTargets.mockRejectedValue(
      Object.assign(new Error("Target inventory could not be retrieved."), {
        code: "NETWORK_ERROR",
      })
    );

    renderWithQueryClient(<TargetList />);

    await waitFor(() =>
      expect(screen.getByText("Unable to load targets")).toBeInTheDocument()
    );
  });

  it("renders target identity, humanized type, and never a raw target_type enum casing mismatch", async () => {
    mockedGetTargets.mockResolvedValue({
      targets: [
        {
          id: "11111111-1111-1111-1111-111111111111",
          target: "10.0.0.5",
          target_type: "IPV4",
          created_at: "2026-07-15T00:00:00Z",
          updated_at: "2026-07-15T00:00:00Z",
        },
      ],
      total: 1,
    });

    renderWithQueryClient(<TargetList />);

    await waitFor(() => expect(screen.getAllByText("10.0.0.5")[0]).toBeInTheDocument());
    expect(screen.getAllByText("IPv4")[0]).toBeInTheDocument();
  });
});
