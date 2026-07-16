/**
 * Mirrors backend/app/schemas/ai.py's AIRecommendationResponse exactly
 * (field names, casing, nullability). Wire-contract type, not a UI view
 * model.
 *
 * AIRecommendation is advisory guidance only — it never owns or influences
 * risk_score/risk_level (Module 06 remains the sole source of those).
 */
export interface AIRecommendationResponse {
  id: string;
  vulnerability_id: string;
  /** The id of the VULNERABILITY-scope RiskAssessment this belongs to —
   * the same value used as {assessment_id} in every /ai/* route. */
  risk_assessment_id: string;
  provider: string;
  model: string;
  prompt_version: string;
  summary: string;
  explanation: string;
  remediation_steps: string[];
  validation_steps: string[];
  cautions: string[];
  generated_at: string;
}
