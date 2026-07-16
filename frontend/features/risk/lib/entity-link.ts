import type { RiskAssessmentResponse } from "@/features/risk/types/risk";

export interface RiskEntityLink {
  href: string;
  label: string;
}

/**
 * Resolves the single, scope-appropriate identity link for a row, using
 * only the FK fields the backend actually populates for that scope (the
 * `chk_risk_assessment_scope_invariants` CHECK constraint guarantees
 * exactly one is set — VULNERABILITY: vulnerability_id, ASSET: asset_id,
 * SCAN: scan_id, ASSESSMENT: none). Never fetches a name/IP to enrich this
 * — that would require an extra request per row (N+1); the id itself is
 * the "authoritative available identity" per this phase's brief.
 */
export function resolveRiskEntityLink(
  assessment: RiskAssessmentResponse
): RiskEntityLink | null {
  switch (assessment.scope) {
    case "VULNERABILITY":
      return assessment.vulnerability_id
        ? { href: `/vulnerabilities/${assessment.vulnerability_id}`, label: assessment.vulnerability_id }
        : null;
    case "ASSET":
      return assessment.asset_id
        ? { href: `/assets/${assessment.asset_id}`, label: assessment.asset_id }
        : null;
    case "SCAN":
      return assessment.scan_id
        ? { href: `/scans/${assessment.scan_id}`, label: assessment.scan_id }
        : null;
    case "ASSESSMENT":
      return null;
  }
}
