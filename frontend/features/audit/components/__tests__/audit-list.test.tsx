import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "@/test/render";

vi.mock("@/features/audit/api/audit-api", () => ({
  auditApi: {
    getAuditEvents: vi.fn(),
  },
}));

import { auditApi } from "@/features/audit/api/audit-api";
import { AuditList } from "@/features/audit/components/audit-list";

const mockedGetAuditEvents = vi.mocked(auditApi.getAuditEvents);

function sampleEvent() {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    event_type: "RISK_CALCULATION_COMPLETED" as const,
    category: "RISK" as const,
    outcome: "SUCCESS" as const,
    actor_type: "ANONYMOUS" as const,
    actor_id: null,
    resource_type: "SCAN" as const,
    resource_id: "scan-1",
    scan_id: "scan-1",
    request_id: "req-1",
    source_ip: "127.0.0.1",
    event_metadata: { risk_score: 7.2, risk_level: "HIGH" },
    occurred_at: "2026-07-15T00:00:00Z",
  };
}

describe("AuditList — read-only surface", () => {
  it("shows the true-empty state", async () => {
    mockedGetAuditEvents.mockResolvedValue({ events: [], total: 0 });
    renderWithQueryClient(<AuditList />);

    await waitFor(() =>
      expect(screen.getByText("No audit events recorded yet")).toBeInTheDocument()
    );
  });

  it("shows the sanitized error state on failure", async () => {
    mockedGetAuditEvents.mockRejectedValue(new Error("network down"));
    renderWithQueryClient(<AuditList />);

    await waitFor(() =>
      expect(screen.getByText("Unable to load audit events")).toBeInTheDocument()
    );
  });

  it("never renders a mutation control anywhere — audit events are read-only", async () => {
    mockedGetAuditEvents.mockResolvedValue({ events: [sampleEvent()], total: 1 });
    renderWithQueryClient(<AuditList />);

    await waitFor(() => expect(screen.getAllByText(/risk calculation completed/i)[0]).toBeInTheDocument());
    expect(screen.queryByRole("button", { name: /delete|edit|retry|replay/i })).not.toBeInTheDocument();
  });

  it("resolves the scan resource link from the row's own data (no extra fetch)", async () => {
    mockedGetAuditEvents.mockResolvedValue({ events: [sampleEvent()], total: 1 });
    renderWithQueryClient(<AuditList />);

    const link = await screen.findByRole("link", { name: "scan-1" });
    expect(link).toHaveAttribute("href", "/scans/scan-1");
    expect(mockedGetAuditEvents).toHaveBeenCalledTimes(1);
  });
});

describe("AuditList — server-side filtering", () => {
  it("maps the category filter to the exact backend enum value", async () => {
    mockedGetAuditEvents.mockResolvedValue({ events: [], total: 0 });
    const user = userEvent.setup();
    renderWithQueryClient(<AuditList />);

    await user.click(screen.getByRole("button", { name: /filter by category/i }));
    await user.click(await screen.findByText("Risk"));

    await waitFor(() =>
      expect(mockedGetAuditEvents).toHaveBeenLastCalledWith(
        expect.objectContaining({ category: "RISK" })
      )
    );
  });

  it("maps the outcome filter to the exact backend enum value", async () => {
    mockedGetAuditEvents.mockResolvedValue({ events: [], total: 0 });
    const user = userEvent.setup();
    renderWithQueryClient(<AuditList />);

    await user.click(screen.getByRole("button", { name: /filter by outcome/i }));
    await user.click(await screen.findByText("Failure"));

    await waitFor(() =>
      expect(mockedGetAuditEvents).toHaveBeenLastCalledWith(
        expect.objectContaining({ outcome: "FAILURE" })
      )
    );
  });

  it("seeds the scan_id filter from a deep-link prop and shows a removable chip", async () => {
    mockedGetAuditEvents.mockResolvedValue({ events: [], total: 0 });
    const user = userEvent.setup();
    renderWithQueryClient(<AuditList initialScanId="scan-42" />);

    await waitFor(() =>
      expect(mockedGetAuditEvents).toHaveBeenCalledWith(
        expect.objectContaining({ scan_id: "scan-42" })
      )
    );
    expect(screen.getByText("scan-42".slice(0, 8))).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /clear scan filter/i }));
    await waitFor(() =>
      expect(mockedGetAuditEvents).toHaveBeenLastCalledWith(
        expect.objectContaining({ scan_id: undefined })
      )
    );
  });

  it("resets to the first page when the active filter set changes", async () => {
    mockedGetAuditEvents.mockResolvedValue({ events: [sampleEvent()], total: 120 });
    const user = userEvent.setup();
    renderWithQueryClient(<AuditList />);

    await waitFor(() => expect(screen.getByRole("button", { name: /next/i })).toBeEnabled());
    await user.click(screen.getByRole("button", { name: /next/i }));
    await waitFor(() =>
      expect(mockedGetAuditEvents).toHaveBeenLastCalledWith(
        expect.objectContaining({ skip: 50 })
      )
    );

    await user.click(screen.getByRole("button", { name: /filter by outcome/i }));
    // The table already renders a "Success" outcome badge for sampleEvent,
    // so scope to the dropdown's own menuitemradio role to disambiguate.
    await user.click(await screen.findByRole("menuitemradio", { name: "Success" }));

    await waitFor(() =>
      expect(mockedGetAuditEvents).toHaveBeenLastCalledWith(
        expect.objectContaining({ skip: 0, outcome: "SUCCESS" })
      )
    );
  });
});
