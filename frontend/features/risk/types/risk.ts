/**
 * Mirrors backend/app/schemas/risk.py exactly (field names, casing,
 * nullability). Wire-contract types, not UI view models.
 *
 * RiskAssessment is Module 06's authoritative, deterministic result — the
 * frontend never calculates, aggregates, or derives a score/level itself.
 */

export type RiskScope = "VULNERABILITY" | "ASSET" | "SCAN" | "ASSESSMENT";
export type RiskLevel = "INFORMATIONAL" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

/**
 * supporting_factors is untyped JSONB on the backend (dict[str, Any]) — its
 * exact shape depends on scope (verified against app/risk_engine/calculator.py
 * and aggregator.py):
 *
 * VULNERABILITY scope: base_score, cvss_used, severity_rating,
 * affected_asset_count, affected_service_count, asset_influence_bonus,
 * service_influence_bonus.
 *
 * ASSET / SCAN / ASSESSMENT scope (all aggregated via the same "maximum"
 * rule): aggregation_method, contributing_count, contributing_entity_id.
 *
 * Kept as a loose record here; components/supporting-factors.tsx is the
 * single allowlisted presentation layer that safely narrows it.
 */
export type RiskSupportingFactors = Record<string, unknown>;

export interface RiskAssessmentResponse {
  id: string;
  scope: RiskScope;
  risk_score: number;
  risk_level: RiskLevel;
  calculation_version: string;
  calculated_at: string;
  supporting_factors: RiskSupportingFactors;
  scan_id: string | null;
  asset_id: string | null;
  vulnerability_id: string | null;
  service_id: string | null;
}

export interface RiskAssessmentListResponse {
  risk_assessments: RiskAssessmentResponse[];
  total: number;
}

/** Maps 1:1 to GET /risk query parameters (app/api/routes/v1/risk.py). */
export interface RiskListFilters {
  scope?: RiskScope;
  risk_level?: RiskLevel;
  scan_id?: string;
}
