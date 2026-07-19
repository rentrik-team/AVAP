import logging
from datetime import UTC, datetime

from app.core.enums import RiskLevel, ScanStatus
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.risk_repository import RiskRepository
from app.schemas.dashboard import (
    DashboardAIStatisticsResponse,
    DashboardAssetStatisticsResponse,
    DashboardReportStatisticsResponse,
    DashboardRiskStatisticsResponse,
    DashboardScanStatisticsResponse,
    DashboardSummaryResponse,
    DashboardVulnerabilityStatisticsResponse,
    RecentAsset,
    RecentReport,
    RecentScan,
    RiskLevelDistribution,
    ScanStatusDistribution,
    TopRiskAsset,
    TopRiskVulnerability,
    VulnerabilitySeverityDistribution,
)

logger = logging.getLogger(__name__)

# Recognized Vulnerability.severity_rating values, matching the Risk Engine's
# own frozen severity fallback mapping (app.risk_engine.rules). Any other
# persisted value is counted as "unknown", never folded into a known bucket.
_SEVERITY_BUCKET_FIELDS = {
    "Critical": "critical",
    "High": "high",
    "Medium": "medium",
    "Low": "low",
    "None": "informational",
}

_RISK_LEVEL_FIELDS = {
    RiskLevel.CRITICAL: "critical",
    RiskLevel.HIGH: "high",
    RiskLevel.MEDIUM: "medium",
    RiskLevel.LOW: "low",
    RiskLevel.INFORMATIONAL: "informational",
}

_SCAN_STATUS_FIELDS = {
    ScanStatus.PENDING: "pending",
    ScanStatus.RUNNING: "running",
    ScanStatus.COMPLETED: "completed",
    ScanStatus.FAILED: "failed",
    ScanStatus.CANCELLED: "cancelled",
}


class DashboardService:
    """Read-only aggregation service for Module 09 dashboard APIs.

    Combines data already persisted by Modules 02/05/06/07/08 into compact
    read models. Never calculates risk, never calls an AI provider, never
    generates a report, and never mutates any entity.
    """

    def __init__(
        self,
        dashboard_repository: DashboardRepository,
        risk_repository: RiskRepository,
        report_repository: ReportRepository,
    ):
        self.dashboard_repository = dashboard_repository
        self.risk_repository = risk_repository
        self.report_repository = report_repository

    def get_summary(self) -> DashboardSummaryResponse:
        assessment = self.risk_repository.get_assessment()
        overall_risk_score = assessment.risk_score if assessment else 0.0
        overall_risk_level = (
            assessment.risk_level if assessment else RiskLevel.INFORMATIONAL
        )

        severity_counts = (
            self.dashboard_repository.get_vulnerability_severity_distribution()
        )
        critical_vulnerability_count = severity_counts.get("Critical", 0)

        risk_level_distribution = (
            self.dashboard_repository.get_asset_risk_level_distribution()
        )
        high_risk_asset_count = risk_level_distribution.get(
            RiskLevel.HIGH, 0
        ) + risk_level_distribution.get(RiskLevel.CRITICAL, 0)

        _, total_reports = self.report_repository.get_all(skip=0, limit=1)

        logger.info(
            "Dashboard aggregation requested",
            extra={"endpoint": "summary"},
        )
        return DashboardSummaryResponse(
            generated_at=datetime.now(UTC),
            total_targets=self.dashboard_repository.count_targets(),
            total_scans=self.dashboard_repository.count_scans(),
            total_assets=self.dashboard_repository.count_assets(),
            unique_vulnerability_count=self.dashboard_repository.count_vulnerabilities(),
            critical_vulnerability_count=critical_vulnerability_count,
            total_reports_generated=total_reports,
            overall_risk_score=overall_risk_score,
            overall_risk_level=overall_risk_level,
            high_risk_asset_count=high_risk_asset_count,
        )

    def get_asset_statistics(self, limit: int) -> DashboardAssetStatisticsResponse:
        recent = self.dashboard_repository.get_recently_discovered_assets(limit)
        logger.info("Dashboard aggregation requested", extra={"endpoint": "assets"})
        return DashboardAssetStatisticsResponse(
            generated_at=datetime.now(UTC),
            total_assets=self.dashboard_repository.count_assets(),
            total_network_services=self.dashboard_repository.count_network_services(),
            recently_discovered_assets=[
                RecentAsset(
                    asset_id=asset.id,
                    ipv4=asset.ipv4,
                    hostname=asset.hostname,
                    discovered_at=asset.created_at,
                )
                for asset in recent
            ],
        )

    def get_vulnerability_statistics(self) -> DashboardVulnerabilityStatisticsResponse:
        raw_counts = self.dashboard_repository.get_vulnerability_severity_distribution()
        bucket_kwargs = dict.fromkeys(_SEVERITY_BUCKET_FIELDS.values(), 0)
        bucket_kwargs["unknown"] = 0
        for raw_rating, count in raw_counts.items():
            field = _SEVERITY_BUCKET_FIELDS.get(raw_rating)
            if field is None:
                bucket_kwargs["unknown"] += count
            else:
                bucket_kwargs[field] += count

        logger.info(
            "Dashboard aggregation requested", extra={"endpoint": "vulnerabilities"}
        )
        return DashboardVulnerabilityStatisticsResponse(
            generated_at=datetime.now(UTC),
            unique_vulnerability_count=self.dashboard_repository.count_vulnerabilities(),
            finding_count=self.dashboard_repository.count_scan_findings(),
            severity_distribution=VulnerabilitySeverityDistribution(**bucket_kwargs),
        )

    def get_risk_statistics(self, top_limit: int) -> DashboardRiskStatisticsResponse:
        assessment = self.risk_repository.get_assessment()
        overall_risk_score = assessment.risk_score if assessment else 0.0
        overall_risk_level = (
            assessment.risk_level if assessment else RiskLevel.INFORMATIONAL
        )

        raw_distribution = self.dashboard_repository.get_asset_risk_level_distribution()
        distribution_kwargs = dict.fromkeys(_RISK_LEVEL_FIELDS.values(), 0)
        for level, count in raw_distribution.items():
            distribution_kwargs[_RISK_LEVEL_FIELDS[level]] = count

        top_assets_rows = self.dashboard_repository.get_top_risk_assets(top_limit)
        top_assets = [
            TopRiskAsset(
                asset_id=row.asset_id,
                ipv4=row.ipv4,
                hostname=row.hostname,
                risk_score=row.risk_score,
                risk_level=row.risk_level,
            )
            for row in top_assets_rows
        ]

        top_vuln_rows = self.dashboard_repository.get_top_risk_vulnerabilities(
            top_limit
        )
        affected_counts = self.dashboard_repository.get_affected_asset_counts(
            [row.vulnerability_id for row in top_vuln_rows]
        )
        top_vulnerabilities = [
            TopRiskVulnerability(
                vulnerability_id=row.vulnerability_id,
                name=row.name,
                cve=row.cve,
                severity_rating=row.severity_rating,
                risk_score=row.risk_score,
                risk_level=row.risk_level,
                affected_asset_count=affected_counts.get(row.vulnerability_id, 0),
            )
            for row in top_vuln_rows
        ]

        logger.info("Dashboard aggregation requested", extra={"endpoint": "risk"})
        return DashboardRiskStatisticsResponse(
            generated_at=datetime.now(UTC),
            overall_risk_score=overall_risk_score,
            overall_risk_level=overall_risk_level,
            risk_level_distribution=RiskLevelDistribution(**distribution_kwargs),
            top_risk_assets=top_assets,
            top_risk_vulnerabilities=top_vulnerabilities,
        )

    def get_scan_statistics(self, limit: int) -> DashboardScanStatisticsResponse:
        raw_status_counts = self.dashboard_repository.get_scan_status_distribution()
        status_kwargs = dict.fromkeys(_SCAN_STATUS_FIELDS.values(), 0)
        for status, count in raw_status_counts.items():
            status_kwargs[_SCAN_STATUS_FIELDS[status]] = count

        completed = status_kwargs["completed"]
        failed = status_kwargs["failed"]
        terminal = completed + failed
        success_rate = round((completed / terminal) * 100, 1) if terminal > 0 else 0.0

        recent = self.dashboard_repository.get_recent_scans(limit)

        logger.info("Dashboard aggregation requested", extra={"endpoint": "scans"})
        return DashboardScanStatisticsResponse(
            generated_at=datetime.now(UTC),
            total_scans=self.dashboard_repository.count_scans(),
            scans_by_status=ScanStatusDistribution(**status_kwargs),
            scan_success_rate_percent=success_rate,
            average_scan_duration_seconds=(
                self.dashboard_repository.get_average_scan_duration_seconds()
            ),
            recent_scans=[
                RecentScan(
                    scan_id=scan.id,
                    target=scan.target.target,
                    target_type=scan.target.target_type,
                    status=scan.status,
                    started_at=scan.started_at,
                    completed_at=scan.completed_at,
                    execution_duration_seconds=scan.execution_duration,
                )
                for scan in recent
            ],
        )

    def get_report_statistics(self, limit: int) -> DashboardReportStatisticsResponse:
        recent_reports, total = self.report_repository.get_all(skip=0, limit=limit)

        logger.info("Dashboard aggregation requested", extra={"endpoint": "reports"})
        return DashboardReportStatisticsResponse(
            generated_at=datetime.now(UTC),
            total_reports_generated=total,
            reports_by_format=self.dashboard_repository.get_reports_by_format(),
            latest_report_generated_at=(
                self.dashboard_repository.get_latest_report_generated_at()
            ),
            recent_reports=[
                RecentReport(
                    report_id=report.id,
                    scan_id=report.scan_id,
                    format=report.format,
                    overall_risk_score=report.overall_risk_score,
                    overall_risk_level=report.overall_risk_level,
                    generated_at=report.generated_at,
                )
                for report in recent_reports
            ],
        )

    def get_ai_statistics(self) -> DashboardAIStatisticsResponse:
        eligible, current = self.dashboard_repository.get_remediation_coverage_counts()
        missing = eligible - current
        coverage_percent = round((current / eligible) * 100, 1) if eligible > 0 else 0.0

        logger.info("Dashboard aggregation requested", extra={"endpoint": "ai"})
        return DashboardAIStatisticsResponse(
            generated_at=datetime.now(UTC),
            total_recommendations=self.dashboard_repository.count_ai_recommendations(),
            recommendations_by_provider=(
                self.dashboard_repository.get_recommendations_by_provider()
            ),
            recommendations_by_model=(
                self.dashboard_repository.get_recommendations_by_model()
            ),
            recommendations_by_severity=(
                self.dashboard_repository.get_recommendations_by_severity()
            ),
            eligible_vulnerability_risk_count=eligible,
            current_recommendation_count=current,
            missing_recommendation_count=missing,
            remediation_coverage_percent=coverage_percent,
        )
