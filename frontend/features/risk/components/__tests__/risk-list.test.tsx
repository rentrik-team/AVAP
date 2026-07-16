import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "@/test/render";

vi.mock("@/features/risk/api/risk-api", () => ({
  riskApi: {
    getRiskAssessments: vi.fn(),
    getRiskByScan: vi.fn(),
    calculateRiskForScan: vi.fn(),
    getRiskSummary: vi.fn(),
  },
}));

import { riskApi } from "@/features/risk/api/risk-api";
import { RiskList } from "@/features/risk/components/risk-list";

const mockedGetRiskAssessments = vi.mocked(riskApi.getRiskAssessments);

function sampleAssessment() {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    scope: "VULNERABILITY" as const,
    risk_score: 8.7,
    risk_level: "HIGH" as const,
    calculation_version: "1.0.0",
    calculated_at: "2026-07-15T00:00:00Z",
    supporting_factors: {
      base_score: 8.0,
      cvss_used: true,
      severity_rating: "High",
      affected_asset_count: 1,
      affected_service_count: 1,
      asset_influence_bonus: 0.0,
      service_influence_bonus: 0.0,
    },
    scan_id: "scan-1",
    asset_id: "asset-1",
    vulnerability_id: "vuln-1",
    service_id: null,
  };
}

describe("RiskList — states", () => {
  it("shows the true-empty state with accurate, non-vulnerability copy", async () => {
    mockedGetRiskAssessments.mockResolvedValue({ risk_assessments: [], total: 0 });
    renderWithQueryClient(<RiskList />);

    await waitFor(() =>
      expect(
        screen.getByText("No risk assessments have been calculated yet")
      ).toBeInTheDocument()
    );
    // Must not conflate "no risk yet" with "no vulnerabilities found" —
    // these are different resources.
    expect(screen.queryByText(/no vulnerabilities found/i)).not.toBeInTheDocument();
  });

  it("shows the sanitized error state on failure", async () => {
    mockedGetRiskAssessments.mockRejectedValue(new Error("network down"));
    renderWithQueryClient(<RiskList />);

    await waitFor(() =>
      expect(screen.getByText("Unable to load risk assessments")).toBeInTheDocument()
    );
  });

  it("renders score and level via RiskScore/RiskLevelBadge — never as a percentage", async () => {
    mockedGetRiskAssessments.mockResolvedValue({
      risk_assessments: [sampleAssessment()],
      total: 1,
    });
    renderWithQueryClient(<RiskList />);

    await waitFor(() => expect(screen.getAllByText("8.7")[0]).toBeInTheDocument());
    expect(screen.getAllByText("/10")[0]).toBeInTheDocument();
    expect(screen.queryByText("87%")).not.toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/8\.7\s*%/);
  });
});

describe("RiskList — server-side filtering", () => {
  it("maps the scope filter to the exact backend enum value", async () => {
    mockedGetRiskAssessments.mockResolvedValue({ risk_assessments: [], total: 0 });
    const user = userEvent.setup();
    renderWithQueryClient(<RiskList />);

    await user.click(screen.getByRole("button", { name: /filter by scope/i }));
    await user.click(await screen.findByText("Vulnerability"));

    await waitFor(() =>
      expect(mockedGetRiskAssessments).toHaveBeenLastCalledWith(
        expect.objectContaining({ scope: "VULNERABILITY", risk_level: undefined })
      )
    );
  });

  it("maps the risk level filter to the exact backend enum value", async () => {
    mockedGetRiskAssessments.mockResolvedValue({ risk_assessments: [], total: 0 });
    const user = userEvent.setup();
    renderWithQueryClient(<RiskList />);

    await user.click(screen.getByRole("button", { name: /filter by risk level/i }));
    await user.click(await screen.findByText("Critical"));

    await waitFor(() =>
      expect(mockedGetRiskAssessments).toHaveBeenLastCalledWith(
        expect.objectContaining({ risk_level: "CRITICAL" })
      )
    );
  });

  it("resets to the first page when the active filter set changes", async () => {
    mockedGetRiskAssessments.mockResolvedValue({
      risk_assessments: [sampleAssessment()],
      total: 120,
    });
    const user = userEvent.setup();
    renderWithQueryClient(<RiskList />);

    await waitFor(() => expect(screen.getByRole("button", { name: /next/i })).toBeEnabled());
    await user.click(screen.getByRole("button", { name: /next/i }));
    await waitFor(() =>
      expect(mockedGetRiskAssessments).toHaveBeenLastCalledWith(
        expect.objectContaining({ skip: 50 })
      )
    );

    await user.click(screen.getByRole("button", { name: /filter by scope/i }));
    await user.click(await screen.findByText("Scan"));

    await waitFor(() =>
      expect(mockedGetRiskAssessments).toHaveBeenLastCalledWith(
        expect.objectContaining({ skip: 0, scope: "SCAN" })
      )
    );
  });
});
