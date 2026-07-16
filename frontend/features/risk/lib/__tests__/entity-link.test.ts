import { describe, expect, it } from "vitest";

import { resolveRiskEntityLink } from "@/features/risk/lib/entity-link";
import type { RiskAssessmentResponse } from "@/features/risk/types/risk";

function assessment(overrides: Partial<RiskAssessmentResponse>): RiskAssessmentResponse {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    scope: "ASSESSMENT",
    risk_score: 5.0,
    risk_level: "MEDIUM",
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

describe("resolveRiskEntityLink", () => {
  it("links a VULNERABILITY-scope row to the vulnerability detail route", () => {
    const link = resolveRiskEntityLink(
      assessment({ scope: "VULNERABILITY", vulnerability_id: "vuln-1" })
    );
    expect(link).toEqual({ href: "/vulnerabilities/vuln-1", label: "vuln-1" });
  });

  it("links an ASSET-scope row to the asset detail route", () => {
    const link = resolveRiskEntityLink(assessment({ scope: "ASSET", asset_id: "asset-1" }));
    expect(link).toEqual({ href: "/assets/asset-1", label: "asset-1" });
  });

  it("links a SCAN-scope row to the scan detail route", () => {
    const link = resolveRiskEntityLink(assessment({ scope: "SCAN", scan_id: "scan-1" }));
    expect(link).toEqual({ href: "/scans/scan-1", label: "scan-1" });
  });

  it("never links an ASSESSMENT-scope row (platform-wide, no entity)", () => {
    expect(resolveRiskEntityLink(assessment({ scope: "ASSESSMENT" }))).toBeNull();
  });
});
