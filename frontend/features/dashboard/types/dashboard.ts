/**
 * Mirrors backend/app/schemas/dashboard.py exactly (field names, casing,
 * nullability). These are wire-contract types, not UI view models — keep
 * them in lockstep with the Pydantic response models, not with how a
 * component happens to render them.
 */

export type RiskLevel = "INFORMATIONAL" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type ScanStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
export type TargetType = "IPV4" | "CIDR" | "HOSTNAME";

export interface ScanStatusDistribution {
  pending: number;
  running: number;
  completed: number;
  failed: number;
}

export interface VulnerabilitySeverityDistribution {
  critical: number;
  high: number;
  medium: number;
  low: number;
  informational: number;
  unknown: number;
}

export interface RiskLevelDistribution {
  critical: number;
  high: number;
  medium: number;
  low: number;
  informational: number;
}

export interface TopRiskAsset {
  asset_id: string;
  ipv4: string;
  hostname: string | null;
  risk_score: number;
  risk_level: RiskLevel;
}

export interface TopRiskVulnerability {
  vulnerability_id: string;
  name: string;
  cve: string | null;
  severity_rating: string;
  risk_score: number;
  risk_level: RiskLevel;
  affected_asset_count: number;
}

export interface RecentScan {
  scan_id: string;
  target: string;
  target_type: TargetType;
  status: ScanStatus;
  started_at: string | null;
  completed_at: string | null;
  execution_duration_seconds: number | null;
}

export interface RecentAsset {
  asset_id: string;
  ipv4: string;
  hostname: string | null;
  discovered_at: string;
}

export interface RecentReport {
  report_id: string;
  scan_id: string;
  format: string;
  overall_risk_score: number;
  overall_risk_level: RiskLevel;
  generated_at: string;
}

export interface DashboardSummaryResponse {
  generated_at: string;
  total_targets: number;
  total_scans: number;
  total_assets: number;
  unique_vulnerability_count: number;
  critical_vulnerability_count: number;
  total_reports_generated: number;
  overall_risk_score: number;
  overall_risk_level: RiskLevel;
  high_risk_asset_count: number;
}

export interface DashboardAssetStatisticsResponse {
  generated_at: string;
  total_assets: number;
  total_network_services: number;
  recently_discovered_assets: RecentAsset[];
}

export interface DashboardVulnerabilityStatisticsResponse {
  generated_at: string;
  unique_vulnerability_count: number;
  finding_count: number;
  severity_distribution: VulnerabilitySeverityDistribution;
}

export interface DashboardRiskStatisticsResponse {
  generated_at: string;
  overall_risk_score: number;
  overall_risk_level: RiskLevel;
  risk_level_distribution: RiskLevelDistribution;
  top_risk_assets: TopRiskAsset[];
  top_risk_vulnerabilities: TopRiskVulnerability[];
}

export interface DashboardScanStatisticsResponse {
  generated_at: string;
  total_scans: number;
  scans_by_status: ScanStatusDistribution;
  scan_success_rate_percent: number;
  average_scan_duration_seconds: number | null;
  recent_scans: RecentScan[];
}

export interface DashboardReportStatisticsResponse {
  generated_at: string;
  total_reports_generated: number;
  reports_by_format: Record<string, number>;
  latest_report_generated_at: string | null;
  recent_reports: RecentReport[];
}

export interface DashboardAIStatisticsResponse {
  generated_at: string;
  total_recommendations: number;
  recommendations_by_provider: Record<string, number>;
  recommendations_by_model: Record<string, number>;
  recommendations_by_severity: Record<string, number>;
  eligible_vulnerability_risk_count: number;
  current_recommendation_count: number;
  missing_recommendation_count: number;
  remediation_coverage_percent: number;
}
