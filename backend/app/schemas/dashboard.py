import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import RiskLevel, ScanStatus, TargetType


class ScanStatusDistribution(BaseModel):
    """Count of scan jobs per lifecycle status (ScanJob.status)."""

    pending: int = Field(0, ge=0)
    running: int = Field(0, ge=0)
    completed: int = Field(0, ge=0)
    failed: int = Field(0, ge=0)

    model_config = ConfigDict(frozen=True)


class VulnerabilitySeverityDistribution(BaseModel):
    """Distribution of unique Vulnerability catalog identities by their
    intrinsic severity_rating (Vulnerability.severity_rating).

    This counts distinct vulnerability identities, never ScanFinding
    observations and never RiskAssessment risk levels. `unknown` captures
    any persisted severity_rating value outside the recognized set
    (None/Low/Medium/High/Critical) so unrecognized data can never silently
    inflate a known severity bucket.
    """

    critical: int = Field(0, ge=0)
    high: int = Field(0, ge=0)
    medium: int = Field(0, ge=0)
    low: int = Field(0, ge=0)
    informational: int = Field(0, ge=0)
    unknown: int = Field(0, ge=0)

    model_config = ConfigDict(frozen=True)


class RiskLevelDistribution(BaseModel):
    """Distribution of deterministic RiskLevel values (Module 06 output only)."""

    critical: int = Field(0, ge=0)
    high: int = Field(0, ge=0)
    medium: int = Field(0, ge=0)
    low: int = Field(0, ge=0)
    informational: int = Field(0, ge=0)

    model_config = ConfigDict(frozen=True)


class TopRiskAsset(BaseModel):
    """One asset's worst (maximum) persisted ASSET-scope risk assessment."""

    asset_id: uuid.UUID
    ipv4: str = Field(..., max_length=45)
    hostname: str | None = Field(None, max_length=253)
    risk_score: float = Field(..., ge=0.0, le=10.0)
    risk_level: RiskLevel

    model_config = ConfigDict(frozen=True)


class TopRiskVulnerability(BaseModel):
    """One vulnerability identity's worst (maximum) persisted
    VULNERABILITY-scope risk assessment across all assets/scans it affects.
    """

    vulnerability_id: uuid.UUID
    name: str = Field(..., max_length=200)
    cve: str | None = Field(None, max_length=20)
    severity_rating: str = Field(..., max_length=20)
    risk_score: float = Field(..., ge=0.0, le=10.0)
    risk_level: RiskLevel
    affected_asset_count: int = Field(..., ge=0)

    model_config = ConfigDict(frozen=True)


class RecentScan(BaseModel):
    """A compact projection of one recent scan job."""

    scan_id: uuid.UUID
    target: str = Field(..., max_length=253)
    target_type: TargetType
    status: ScanStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    execution_duration_seconds: float | None = Field(None, ge=0.0)

    model_config = ConfigDict(frozen=True)


class RecentAsset(BaseModel):
    """A compact projection of one recently discovered asset."""

    asset_id: uuid.UUID
    ipv4: str = Field(..., max_length=45)
    hostname: str | None = Field(None, max_length=253)
    discovered_at: datetime

    model_config = ConfigDict(frozen=True)


class RecentReport(BaseModel):
    """A compact projection of one recently generated report."""

    report_id: uuid.UUID
    scan_id: uuid.UUID
    format: str = Field(..., max_length=10)
    overall_risk_score: float = Field(..., ge=0.0, le=10.0)
    overall_risk_level: RiskLevel
    generated_at: datetime

    model_config = ConfigDict(frozen=True)


class DashboardSummaryResponse(BaseModel):
    """Executive-level platform overview (GET /dashboard/summary)."""

    generated_at: datetime
    total_targets: int = Field(..., ge=0)
    total_scans: int = Field(..., ge=0)
    total_assets: int = Field(..., ge=0)
    unique_vulnerability_count: int = Field(..., ge=0)
    critical_vulnerability_count: int = Field(..., ge=0)
    total_reports_generated: int = Field(..., ge=0)
    overall_risk_score: float = Field(..., ge=0.0, le=10.0)
    overall_risk_level: RiskLevel
    high_risk_asset_count: int = Field(..., ge=0)

    model_config = ConfigDict(frozen=True)


class DashboardAssetStatisticsResponse(BaseModel):
    """Asset inventory metrics (GET /dashboard/assets)."""

    generated_at: datetime
    total_assets: int = Field(..., ge=0)
    total_network_services: int = Field(..., ge=0)
    recently_discovered_assets: list[RecentAsset] = Field(..., max_length=50)

    model_config = ConfigDict(frozen=True)


class DashboardVulnerabilityStatisticsResponse(BaseModel):
    """Vulnerability catalog metrics (GET /dashboard/vulnerabilities).

    `unique_vulnerability_count` and `finding_count` are deliberately
    distinct: the former counts Vulnerability catalog identities, the
    latter counts ScanFinding observations across all scans.
    """

    generated_at: datetime
    unique_vulnerability_count: int = Field(..., ge=0)
    finding_count: int = Field(..., ge=0)
    severity_distribution: VulnerabilitySeverityDistribution

    model_config = ConfigDict(frozen=True)


class DashboardRiskStatisticsResponse(BaseModel):
    """Deterministic risk posture metrics (GET /dashboard/risk).

    Sourced exclusively from Module 06 RiskAssessment rows. Never derived
    from Vulnerability.severity_rating.
    """

    generated_at: datetime
    overall_risk_score: float = Field(..., ge=0.0, le=10.0)
    overall_risk_level: RiskLevel
    risk_level_distribution: RiskLevelDistribution
    top_risk_assets: list[TopRiskAsset] = Field(..., max_length=50)
    top_risk_vulnerabilities: list[TopRiskVulnerability] = Field(..., max_length=50)

    model_config = ConfigDict(frozen=True)


class DashboardScanStatisticsResponse(BaseModel):
    """Scan execution/operational metrics (GET /dashboard/scans)."""

    generated_at: datetime
    total_scans: int = Field(..., ge=0)
    scans_by_status: ScanStatusDistribution
    scan_success_rate_percent: float = Field(..., ge=0.0, le=100.0)
    average_scan_duration_seconds: float | None = Field(None, ge=0.0)
    recent_scans: list[RecentScan] = Field(..., max_length=50)

    model_config = ConfigDict(frozen=True)


class DashboardReportStatisticsResponse(BaseModel):
    """Report generation metrics sourced from Module 08 Report metadata only
    (GET /dashboard/reports). Never derived from the filesystem.
    """

    generated_at: datetime
    total_reports_generated: int = Field(..., ge=0)
    reports_by_format: dict[str, int]
    latest_report_generated_at: datetime | None = None
    recent_reports: list[RecentReport] = Field(..., max_length=50)

    model_config = ConfigDict(frozen=True)


class DashboardAIStatisticsResponse(BaseModel):
    """AI recommendation availability metrics (GET /dashboard/ai).

    This reports recommendation *availability*, not remediation
    effectiveness. `current_recommendation_count` only counts
    VULNERABILITY-scope risk assessments with at least one recommendation
    whose `generated_at >= risk_assessment.calculated_at` (Module 07's own
    freshness rule). Dashboard aggregation never triggers AI generation.
    """

    generated_at: datetime
    total_recommendations: int = Field(..., ge=0)
    recommendations_by_provider: dict[str, int]
    recommendations_by_model: dict[str, int]
    recommendations_by_severity: dict[str, int]
    eligible_vulnerability_risk_count: int = Field(..., ge=0)
    current_recommendation_count: int = Field(..., ge=0)
    missing_recommendation_count: int = Field(..., ge=0)
    remediation_coverage_percent: float = Field(..., ge=0.0, le=100.0)

    model_config = ConfigDict(frozen=True)
