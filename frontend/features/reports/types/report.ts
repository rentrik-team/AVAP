/**
 * Mirrors backend/app/schemas/report.py's ReportResponse exactly (field
 * names, casing, nullability). Wire-contract type, not a UI view model.
 *
 * Reports are immutable, versioned artifacts — there is no update endpoint,
 * and no server-side filesystem path is ever exposed here.
 */
export type RiskLevel = "INFORMATIONAL" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface ReportResponse {
  id: string;
  scan_id: string;
  format: string;
  report_template_version: string;
  risk_calculation_version: string;
  overall_risk_score: number;
  overall_risk_level: RiskLevel;
  vulnerability_count: number;
  ai_recommendations_included: number;
  file_size_bytes: number;
  generated_at: string;
}

export interface ReportListResponse {
  reports: ReportResponse[];
  total: number;
}

/** Maps 1:1 to GET /reports query parameters (app/api/routes/v1/reports.py). */
export interface ReportListFilters {
  scan_id?: string;
}
