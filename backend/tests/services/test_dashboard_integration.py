"""End-to-end integration: Module 05 persisted findings -> Module 06 risk
calculation -> Module 07 validated AI recommendation (current and stale) ->
Module 08 persisted report metadata -> Module 09 dashboard aggregation APIs.

Exercises the real repository/service/API boundaries; DashboardService is
never mocked.
"""

from datetime import timedelta

from fastapi.testclient import TestClient

from app.ai.manager import AIManager
from app.ai.provider import AIProviderResponse
from app.core.config import Settings
from app.core.enums import RiskScope, ScanStatus, TargetType
from app.models.ai_recommendation import AIRecommendation
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.parsers.models import (
    AssessmentPackage,
    ParsedHost,
    ParsedService,
    ParsedVulnerability,
)
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.network_service_repository import NetworkServiceRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.ai_service import AIService
from app.services.audit_service import AuditService
from app.services.inventory_service import InventoryService
from app.services.report_service import ReportService
from app.services.risk_service import RiskService


class _FakeProviderBoundaryManager(AIManager):
    """A fake at the real Module 07 AI Manager interface boundary, used only
    to prepare a genuine, validated AIRecommendation fixture via the actual
    Module 07 service.
    """

    def resolve_provider_name(self):
        return "openrouter"

    def resolve_model_name(self):
        return "fake-integration-model"

    def generate(self, prompt):
        content = (
            '{"summary": "Upgrade the vulnerable service.", '
            '"explanation": "The detected version is affected by known CVEs.", '
            '"remediation_steps": ["Apply the latest security patch."], '
            '"validation_steps": ["Confirm the updated version."], '
            '"cautions": ["Restart during a maintenance window."]}'
        )
        return AIProviderResponse(
            content=content, provider="openrouter", model="fake-integration-model"
        )


def test_module05_through_module09_end_to_end(client: TestClient, db_session, tmp_path):
    # --- Module 05: two distinct vulnerability identities, multiple findings ---
    target = Target(target="203.0.113.90", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()

    scan_job = ScanJob(target_id=target.id, status=ScanStatus.RUNNING, scan_type="full")
    db_session.add(scan_job)
    db_session.flush()

    audit_service = AuditService(AuditRepository(db_session))
    inventory_service = InventoryService(
        db_session,
        AssetRepository(db_session),
        VulnerabilityRepository(db_session),
        ScanRepository(db_session),
        audit_service,
    )

    high_vuln = ParsedVulnerability(
        name="Outdated OpenSSH",
        severity_score=8.2,
        severity_rating="High",
        cve="CVE-2024-9200",
    )
    critical_vuln = ParsedVulnerability(
        name="Unpatched OpenSSL",
        severity_score=9.5,
        severity_rating="Critical",
        cve="CVE-2024-9300",
    )
    host = ParsedHost(
        ipv4="203.0.113.90",
        hostname="dashboard-integration-host",
        services=[
            ParsedService(
                port=22,
                protocol="tcp",
                service_name="ssh",
                product="OpenSSH",
                version="7.4",
                vulnerabilities=[high_vuln],
            ),
            ParsedService(
                port=443,
                protocol="tcp",
                service_name="https",
                product="OpenSSL",
                version="1.0.2",
                vulnerabilities=[critical_vuln],
            ),
        ],
    )
    package = AssessmentPackage(
        scan_id=scan_job.id, scanner_type="OPENVAS", parsed_hosts=[host]
    )
    inventory_service.process_assessment_package(package)

    # --- Module 06: calculate deterministic risk ---
    risk_repository = RiskRepository(db_session)
    risk_service = RiskService(
        session=db_session,
        risk_repository=risk_repository,
        scan_repository=ScanRepository(db_session),
        asset_repository=AssetRepository(db_session),
        scan_finding_repository=ScanFindingRepository(db_session),
        audit_service=audit_service,
    )
    scan_risk = risk_service.calculate_risk_for_scan(scan_job.id)

    vulnerability_risks = risk_repository.get_by_scan_and_scope(
        scan_job.id, RiskScope.VULNERABILITY
    )
    assert len(vulnerability_risks) == 2

    # --- Module 07: one current recommendation, one deliberately stale ---
    ai_recommendation_repository = AIRecommendationRepository(db_session)
    ai_service = AIService(
        session=db_session,
        ai_recommendation_repository=ai_recommendation_repository,
        risk_repository=risk_repository,
        vulnerability_repository=VulnerabilityRepository(db_session),
        network_service_repository=NetworkServiceRepository(db_session),
        audit_service=audit_service,
        ai_manager=_FakeProviderBoundaryManager(),
    )
    current_target_risk = vulnerability_risks[0]
    stale_target_risk = vulnerability_risks[1]

    ai_service.generate_recommendation(current_target_risk.id)
    ai_service.generate_recommendation(stale_target_risk.id)
    # Force the second recommendation stale by pre-dating it relative to a
    # risk recalculation, mirroring Module 07's own freshness rule exactly.
    stale_recommendation = ai_recommendation_repository.get_by_risk_assessment(
        stale_target_risk.id
    )
    assert stale_recommendation is not None
    stale_recommendation.generated_at = stale_target_risk.calculated_at - timedelta(
        hours=1
    )
    db_session.flush()
    db_session.commit()

    # --- Module 08: generate a report through the real REST API ---
    from app.api.routes.v1.reports import get_report_service
    from app.main import app

    def override_report_service():
        return ReportService(
            session=db_session,
            report_repository=ReportRepository(db_session),
            scan_repository=ScanRepository(db_session),
            risk_repository=risk_repository,
            asset_repository=AssetRepository(db_session),
            vulnerability_repository=VulnerabilityRepository(db_session),
            network_service_repository=NetworkServiceRepository(db_session),
            scan_finding_repository=ScanFindingRepository(db_session),
            ai_recommendation_repository=ai_recommendation_repository,
            audit_service=audit_service,
            settings=Settings(_env_file=None, report_output_directory=str(tmp_path)),
        )

    app.dependency_overrides[get_report_service] = override_report_service
    try:
        generate_response = client.post(
            "/api/v1/reports", json={"scan_id": str(scan_job.id)}
        )
        assert generate_response.status_code == 201
    finally:
        app.dependency_overrides.pop(get_report_service, None)

    # --- Module 09: dashboard aggregation over the above persisted state ---

    summary = client.get("/api/v1/dashboard/summary").json()["data"]
    assert summary["total_targets"] == 1
    assert summary["total_scans"] == 1
    assert summary["total_assets"] == 1
    assert summary["unique_vulnerability_count"] == 2
    assert summary["critical_vulnerability_count"] == 1
    assert summary["total_reports_generated"] == 1
    assert summary["overall_risk_score"] == scan_risk.risk_score

    vuln_stats = client.get("/api/v1/dashboard/vulnerabilities").json()["data"]
    assert vuln_stats["unique_vulnerability_count"] == 2
    assert vuln_stats["finding_count"] == 2
    assert vuln_stats["severity_distribution"]["critical"] == 1
    assert vuln_stats["severity_distribution"]["high"] == 1

    risk_stats = client.get("/api/v1/dashboard/risk").json()["data"]
    assert risk_stats["overall_risk_score"] == scan_risk.risk_score
    assert len(risk_stats["top_risk_vulnerabilities"]) == 2
    # Worst vulnerability-scope risk ranked first.
    assert (
        risk_stats["top_risk_vulnerabilities"][0]["risk_score"]
        >= risk_stats["top_risk_vulnerabilities"][1]["risk_score"]
    )
    assert len(risk_stats["top_risk_assets"]) == 1

    ai_stats = client.get("/api/v1/dashboard/ai").json()["data"]
    assert ai_stats["eligible_vulnerability_risk_count"] == 2
    assert ai_stats["current_recommendation_count"] == 1
    assert ai_stats["missing_recommendation_count"] == 1
    assert ai_stats["remediation_coverage_percent"] == 50.0

    report_stats = client.get("/api/v1/dashboard/reports").json()["data"]
    assert report_stats["total_reports_generated"] == 1
    assert report_stats["reports_by_format"] == {"PDF": 1}
    assert len(report_stats["recent_reports"]) == 1

    scan_stats = client.get("/api/v1/dashboard/scans").json()["data"]
    assert scan_stats["total_scans"] == 1
    assert len(scan_stats["recent_scans"]) == 1
    assert scan_stats["recent_scans"][0]["target"] == "203.0.113.90"

    asset_stats = client.get("/api/v1/dashboard/assets").json()["data"]
    assert asset_stats["total_assets"] == 1
    assert asset_stats["total_network_services"] == 2
    assert len(asset_stats["recently_discovered_assets"]) == 1

    # --- Module 06/07/08 remain authoritative and untouched by dashboard reads ---
    db_session.refresh(scan_risk)
    assert scan_risk.risk_score == risk_stats["overall_risk_score"]
    assert db_session.query(AIRecommendation).count() == 2
