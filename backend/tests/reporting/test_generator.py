import json
from datetime import UTC, datetime, timedelta

import pytest

from app.ai.provider import AIProviderResponse
from app.core.enums import RiskScope, ScanStatus, TargetType
from app.core.exceptions import InsufficientReportDataException
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.parsers.models import (
    AssessmentPackage,
    ParsedHost,
    ParsedService,
    ParsedVulnerability,
)
from app.reporting.generator import REPORT_TEMPLATE_VERSION, build_report_data
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.network_service_repository import NetworkServiceRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.ai_service import AIService
from app.services.inventory_service import InventoryService
from app.services.risk_service import RiskService


class _FakeAIManager:
    def __init__(self, content=None):
        self.content = content or json.dumps(
            {
                "summary": "Upgrade required.",
                "explanation": "The service is outdated.",
                "remediation_steps": ["Apply the vendor patch."],
                "validation_steps": ["Re-scan the host."],
                "cautions": ["Schedule downtime."],
            }
        )

    def resolve_provider_name(self):
        return "openrouter"

    def resolve_model_name(self):
        return "fake-model"

    def generate(self, prompt):
        return AIProviderResponse(
            content=self.content, provider="openrouter", model="fake-model"
        )


class _Repos:
    def __init__(self, db_session):
        self.asset = AssetRepository(db_session)
        self.vulnerability = VulnerabilityRepository(db_session)
        self.scan = ScanRepository(db_session)
        self.risk = RiskRepository(db_session)
        self.service = NetworkServiceRepository(db_session)
        self.scan_finding = ScanFindingRepository(db_session)
        self.ai_recommendation = AIRecommendationRepository(db_session)


def _seed_scan(
    db_session,
    ipv4="203.0.113.10",
    severity_score=7.5,
    severity_rating="High",
    cve="CVE-2024-1000",
    port=443,
    with_ai=False,
):
    repos = _Repos(db_session)

    target = Target(target=ipv4, target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()

    scan_job = ScanJob(target_id=target.id, status=ScanStatus.RUNNING, scan_type="full")
    db_session.add(scan_job)
    db_session.flush()

    inventory_service = InventoryService(
        db_session, repos.asset, repos.vulnerability, repos.scan
    )
    vuln = ParsedVulnerability(
        name="Outdated Service",
        severity_score=severity_score,
        severity_rating=severity_rating,
        cve=cve,
    )
    parsed_service = ParsedService(
        port=port,
        protocol="tcp",
        service_name="https",
        product="Acme",
        version="1.0",
        vulnerabilities=[vuln],
    )
    host = ParsedHost(
        ipv4=ipv4,
        hostname=f"host-{port}.local",
        operating_system="Linux",
        services=[parsed_service],
    )
    package = AssessmentPackage(
        scan_id=scan_job.id, scanner_type="OPENVAS", parsed_hosts=[host]
    )
    inventory_service.process_assessment_package(package)

    risk_service = RiskService(
        session=db_session,
        risk_repository=repos.risk,
        scan_repository=repos.scan,
        asset_repository=repos.asset,
        scan_finding_repository=repos.scan_finding,
    )
    risk_service.calculate_risk_for_scan(scan_job.id)

    if with_ai:
        vulnerability_risks = repos.risk.get_by_scan_and_scope(
            scan_job.id, RiskScope.VULNERABILITY
        )
        ai_service = AIService(
            session=db_session,
            ai_recommendation_repository=repos.ai_recommendation,
            risk_repository=repos.risk,
            vulnerability_repository=repos.vulnerability,
            network_service_repository=repos.service,
            ai_manager=_FakeAIManager(),
        )
        for risk in vulnerability_risks:
            ai_service.generate_recommendation(risk.id)

    return scan_job, repos


def _build(db_session, scan_job, repos):
    scan_risk = repos.risk.get_by_scan(scan_job.id)
    return build_report_data(
        scan_job=scan_job,
        scan_risk=scan_risk,
        generated_at=datetime.now(UTC),
        risk_repository=repos.risk,
        asset_repository=repos.asset,
        vulnerability_repository=repos.vulnerability,
        network_service_repository=repos.service,
        scan_finding_repository=repos.scan_finding,
        ai_recommendation_repository=repos.ai_recommendation,
    )


# --- Valid assembly ---


def test_build_report_data_valid_scan_context(db_session):
    scan_job, repos = _seed_scan(db_session)
    report_data = _build(db_session, scan_job, repos)

    assert report_data.metadata.scan_id == scan_job.id
    assert report_data.metadata.target == "203.0.113.10"
    assert report_data.metadata.report_template_version == REPORT_TEMPLATE_VERSION
    assert len(report_data.findings) == 1
    assert report_data.findings[0].risk_score == 7.5
    assert len(report_data.assets) == 1


def test_build_report_data_includes_deterministic_risk_from_module06(db_session):
    scan_job, repos = _seed_scan(
        db_session, severity_score=9.5, severity_rating="Critical"
    )
    report_data = _build(db_session, scan_job, repos)

    assert report_data.executive_summary.overall_risk_score == 9.5
    assert report_data.executive_summary.overall_risk_level.value == "CRITICAL"
    assert report_data.executive_summary.severity_distribution.critical == 1


def test_build_report_data_affected_service_included(db_session):
    scan_job, repos = _seed_scan(db_session, port=8443)
    report_data = _build(db_session, scan_job, repos)

    service = report_data.findings[0].affected_service
    assert service is not None
    assert service.port == 8443
    assert service.product == "Acme"


# --- AI recommendation inclusion / freshness ---


def test_build_report_data_includes_current_ai_recommendation(db_session):
    scan_job, repos = _seed_scan(db_session, with_ai=True)
    report_data = _build(db_session, scan_job, repos)

    remediation = report_data.findings[0].remediation
    assert remediation is not None
    assert remediation.provider == "openrouter"
    assert remediation.remediation_steps == ["Apply the vendor patch."]


def test_build_report_data_missing_ai_recommendation_is_none(db_session):
    scan_job, repos = _seed_scan(db_session, with_ai=False)
    report_data = _build(db_session, scan_job, repos)

    assert report_data.findings[0].remediation is None


def test_build_report_data_excludes_stale_ai_recommendation(db_session):
    scan_job, repos = _seed_scan(db_session, with_ai=True)

    # Simulate the recommendation becoming stale relative to its risk assessment.
    vulnerability_risks = repos.risk.get_by_scan_and_scope(
        scan_job.id, RiskScope.VULNERABILITY
    )
    risk = vulnerability_risks[0]
    recommendation = repos.ai_recommendation.get_by_risk_assessment(risk.id)
    recommendation.generated_at = risk.calculated_at - timedelta(days=1)
    db_session.commit()

    report_data = _build(db_session, scan_job, repos)
    assert report_data.findings[0].remediation is None


# --- Missing required risk data ---


def test_build_report_data_requires_scan_risk(db_session):
    """No VULNERABILITY-scope risk for a finding means it is excluded, and if
    that leaves zero reportable findings, generation must fail explicitly.
    """
    target = Target(target="203.0.113.20", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()
    scan_job = ScanJob(
        target_id=target.id, status=ScanStatus.COMPLETED, scan_type="full"
    )
    db_session.add(scan_job)
    db_session.flush()

    repos = _Repos(db_session)
    with pytest.raises(InsufficientReportDataException):
        build_report_data(
            scan_job=scan_job,
            scan_risk=None,  # type: ignore[arg-type]
            generated_at=datetime.now(UTC),
            risk_repository=repos.risk,
            asset_repository=repos.asset,
            vulnerability_repository=repos.vulnerability,
            network_service_repository=repos.service,
            scan_finding_repository=repos.scan_finding,
            ai_recommendation_repository=repos.ai_recommendation,
        )


# --- No ORM leakage ---


def test_build_report_data_contains_no_orm_objects(db_session):
    scan_job, repos = _seed_scan(db_session)
    report_data = _build(db_session, scan_job, repos)

    for finding in report_data.findings:
        assert isinstance(finding.vulnerability_name, str)
        assert isinstance(finding.asset_ipv4, str)
        assert not hasattr(finding, "_sa_instance_state")
    assert not hasattr(report_data, "_sa_instance_state")


# --- Deterministic assembly ---


def test_build_report_data_is_deterministic_for_identical_state(db_session):
    scan_job, repos = _seed_scan(db_session)
    generated_at = datetime.now(UTC)
    scan_risk = repos.risk.get_by_scan(scan_job.id)

    first = build_report_data(
        scan_job=scan_job,
        scan_risk=scan_risk,
        generated_at=generated_at,
        risk_repository=repos.risk,
        asset_repository=repos.asset,
        vulnerability_repository=repos.vulnerability,
        network_service_repository=repos.service,
        scan_finding_repository=repos.scan_finding,
        ai_recommendation_repository=repos.ai_recommendation,
    )
    second = build_report_data(
        scan_job=scan_job,
        scan_risk=scan_risk,
        generated_at=generated_at,
        risk_repository=repos.risk,
        asset_repository=repos.asset,
        vulnerability_repository=repos.vulnerability,
        network_service_repository=repos.service,
        scan_finding_repository=repos.scan_finding,
        ai_recommendation_repository=repos.ai_recommendation,
    )
    assert first == second
