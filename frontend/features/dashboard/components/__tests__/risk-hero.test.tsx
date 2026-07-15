import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "@/test/render";

vi.mock("@/features/dashboard/api/dashboard-api", () => ({
  dashboardApi: {
    getSummary: vi.fn(),
  },
}));

import { dashboardApi } from "@/features/dashboard/api/dashboard-api";
import { RiskHero } from "@/features/dashboard/components/risk-hero";

const mockedGetSummary = vi.mocked(dashboardApi.getSummary);

const SUMMARY_FIXTURE = {
  generated_at: "2026-07-15T00:00:00Z",
  total_targets: 4,
  total_scans: 6,
  total_assets: 10,
  unique_vulnerability_count: 12,
  critical_vulnerability_count: 3,
  total_reports_generated: 2,
  overall_risk_score: 8.4,
  overall_risk_level: "HIGH" as const,
  high_risk_asset_count: 5,
};

describe("RiskHero", () => {
  it("renders a loading skeleton before data arrives", () => {
    mockedGetSummary.mockReturnValue(new Promise(() => {})); // never resolves
    renderWithQueryClient(<RiskHero />);

    expect(screen.queryByText("Overall Security Posture")).not.toBeInTheDocument();
  });

  it("renders the real risk score and risk level distinctly once loaded — never fabricated or recalculated", async () => {
    mockedGetSummary.mockResolvedValue(SUMMARY_FIXTURE);
    renderWithQueryClient(<RiskHero />);

    await waitFor(() => expect(screen.getByText("Overall Security Posture")).toBeInTheDocument());

    // Risk score (numeric) and risk level (categorical) render as two
    // distinct pieces of UI, not conflated into one element.
    expect(screen.getByText("8.4")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument(); // critical vulnerability count
    expect(screen.getByText("5")).toBeInTheDocument(); // high-risk asset count
  });

  it("shows an actionable, sanitized error state on failure — never a raw error message", async () => {
    mockedGetSummary.mockRejectedValue(new Error("connect ECONNREFUSED 127.0.0.1:8000"));
    renderWithQueryClient(<RiskHero />);

    await waitFor(() =>
      expect(screen.getByText("Unable to load security posture")).toBeInTheDocument()
    );
    expect(screen.queryByText(/ECONNREFUSED/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  it("retries the query when the user clicks Try again", async () => {
    mockedGetSummary.mockRejectedValueOnce(new Error("boom"));
    mockedGetSummary.mockResolvedValueOnce(SUMMARY_FIXTURE);
    const user = userEvent.setup();
    renderWithQueryClient(<RiskHero />);

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument()
    );
    await user.click(screen.getByRole("button", { name: /try again/i }));

    await waitFor(() => expect(screen.getByText("8.4")).toBeInTheDocument());
    expect(mockedGetSummary).toHaveBeenCalledTimes(2);
  });
});
