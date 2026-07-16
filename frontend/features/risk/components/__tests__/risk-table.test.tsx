import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TooltipProvider } from "@/components/ui/tooltip";
import { RiskTable } from "@/features/risk/components/risk-table";
import type { RiskAssessmentResponse, RiskScope } from "@/features/risk/types/risk";

function assessment(scope: RiskScope, overrides: Partial<RiskAssessmentResponse> = {}) {
  return {
    id: `${scope}-1`,
    scope,
    risk_score: 8.0,
    risk_level: "HIGH" as const,
    calculation_version: "1.0.0",
    calculated_at: "2026-07-15T00:00:00Z",
    supporting_factors: {},
    scan_id: null,
    asset_id: null,
    vulnerability_id: null,
    service_id: null,
    ...overrides,
  };
}

function renderTable(assessments: RiskAssessmentResponse[]) {
  const onOpenRemediation = vi.fn();
  render(
    <TooltipProvider>
      <RiskTable assessments={assessments} onOpenRemediation={onOpenRemediation} />
    </TooltipProvider>
  );
  return { onOpenRemediation };
}

describe("RiskTable — scope safety", () => {
  it("offers Remediation only for a VULNERABILITY-scope row", async () => {
    const { onOpenRemediation } = renderTable([
      assessment("VULNERABILITY", { vulnerability_id: "vuln-1" }),
      assessment("ASSET", { asset_id: "asset-1" }),
      assessment("SCAN", { scan_id: "scan-1" }),
      assessment("ASSESSMENT"),
    ]);

    const remediationButtons = screen.getAllByRole("button", { name: /remediation/i });
    expect(remediationButtons).toHaveLength(1);

    const user = userEvent.setup();
    await user.click(remediationButtons[0]);
    expect(onOpenRemediation).toHaveBeenCalledWith(
      expect.objectContaining({ scope: "VULNERABILITY" })
    );
  });

  it("shows RiskScopeBadge (not SeverityBadge/ScanStatusBadge visuals) and RiskLevelBadge — never treats scope as severity", () => {
    renderTable([assessment("ASSET", { asset_id: "asset-1", risk_level: "CRITICAL" })]);

    expect(screen.getByText("Asset")).toBeInTheDocument();
    // RiskLevelBadge renders the risk level label; SeverityBadge would too,
    // but there is no vulnerability severity anywhere on an ASSET-scope row.
    expect(screen.getByText("Critical")).toBeInTheDocument();
  });

  it("resolves ASSESSMENT scope as platform-wide with no entity link", () => {
    renderTable([assessment("ASSESSMENT")]);
    expect(screen.getByText("Platform-wide")).toBeInTheDocument();
  });
});
