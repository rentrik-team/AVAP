import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import RiskLevel, ScanStatus, TargetType


class SeverityDistribution(BaseModel):
    """Count of vulnerability findings per risk level within one scan."""

    critical: int = Field(0, ge=0)
    high: int = Field(0, ge=0)
    medium: int = Field(0, ge=0)
    low: int = Field(0, ge=0)
    informational: int = Field(0, ge=0)

    model_config = ConfigDict(frozen=True)


class ExecutiveSummary(BaseModel):
    """Deterministic, statistics-only summary. Never AI-generated prose."""

    overall_risk_score: float = Field(..., ge=0.0, le=10.0)
    overall_risk_level: RiskLevel
    total_assets: int = Field(..., ge=0)
    total_vulnerabilities: int = Field(..., ge=0)
    severity_distribution: SeverityDistribution

    model_config = ConfigDict(frozen=True)


class AffectedService(BaseModel):
    """A network service on which a finding was observed."""

    port: int = Field(..., ge=0, le=65535)
    protocol: str = Field(..., max_length=10)
    service_name: str = Field(..., max_length=50)
    product: str | None = Field(None, max_length=100)
    version: str | None = Field(None, max_length=50)

    model_config = ConfigDict(frozen=True)


class RemediationGuidance(BaseModel):
    """Advisory AI-assisted remediation content for one finding.

    Included only when a current (non-stale) AIRecommendation exists for the
    finding's own VULNERABILITY-scope RiskAssessment. Never influences risk.
    """

    summary: str = Field(..., max_length=500)
    explanation: str = Field(..., max_length=4000)
    remediation_steps: list[str]
    validation_steps: list[str]
    cautions: list[str]
    provider: str = Field(..., max_length=50)
    model: str = Field(..., max_length=100)
    generated_at: datetime

    model_config = ConfigDict(frozen=True)


class FindingDetail(BaseModel):
    """One deterministic vulnerability finding within the reported scan."""

    vulnerability_id: uuid.UUID
    vulnerability_name: str = Field(..., max_length=200)
    cve: str | None = Field(None, max_length=20)
    description: str | None = Field(None, max_length=3000)
    severity_rating: str = Field(..., max_length=20)
    severity_score: float = Field(..., ge=0.0, le=10.0)
    risk_score: float = Field(..., ge=0.0, le=10.0)
    risk_level: RiskLevel
    asset_ipv4: str = Field(..., max_length=45)
    asset_hostname: str | None = Field(None, max_length=253)
    affected_service: AffectedService | None = None
    remediation: RemediationGuidance | None = None

    model_config = ConfigDict(frozen=True)


class AssetSummary(BaseModel):
    """Deterministic per-asset risk rollup within the reported scan."""

    asset_id: uuid.UUID
    ipv4: str = Field(..., max_length=45)
    hostname: str | None = Field(None, max_length=253)
    operating_system: str | None = Field(None, max_length=253)
    risk_score: float = Field(..., ge=0.0, le=10.0)
    risk_level: RiskLevel
    vulnerability_count: int = Field(..., ge=0)

    model_config = ConfigDict(frozen=True)


class ReportMetadata(BaseModel):
    """Point-in-time generation context for one report."""

    scan_id: uuid.UUID
    target: str = Field(..., max_length=253)
    target_type: TargetType
    scan_status: ScanStatus
    scan_started_at: datetime | None = None
    scan_completed_at: datetime | None = None
    generated_at: datetime
    report_template_version: str = Field(..., max_length=20)
    risk_calculation_version: str = Field(..., max_length=20)

    model_config = ConfigDict(frozen=True)


class ReportData(BaseModel):
    """The complete, validated, provider- and format-neutral report contract.

    Built exclusively from already-persisted Module 05/06/07 data by the
    Report Data Builder. Never constructed from raw ORM objects, and never
    mutated after construction (frozen). This is the only input the PDF
    renderer receives; the renderer never queries the database itself.
    """

    metadata: ReportMetadata
    executive_summary: ExecutiveSummary
    assets: list[AssetSummary]
    findings: list[FindingDetail]

    model_config = ConfigDict(frozen=True)


class GenerateReportRequest(BaseModel):
    """Request body for triggering report generation.

    The only report subject a caller may select is the source scan; no
    report body content, risk values, or file paths are ever accepted.
    """

    scan_id: uuid.UUID


class ReportResponse(BaseModel):
    """API response model for persisted report metadata."""

    id: uuid.UUID
    scan_id: uuid.UUID
    format: str
    report_template_version: str
    risk_calculation_version: str
    overall_risk_score: float
    overall_risk_level: RiskLevel
    vulnerability_count: int
    ai_recommendations_included: int
    file_size_bytes: int
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportListResponse(BaseModel):
    """Response model for a paginated list of report metadata records."""

    reports: list[ReportResponse]
    total: int
