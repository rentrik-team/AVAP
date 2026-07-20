"""End-to-end integration: Module 05 persisted findings -> Module 06 risk
calculation -> Module 07 validated AI recommendation (via a fake provider
through the real provider boundary) -> Module 08 report data assembly ->
PDF generation -> report metadata persistence -> Report API retrieval ->
PDF download.
"""

from fastapi.testclient import TestClient

from app.ai.manager import AIManager
from app.ai.provider import AIProviderResponse
from app.core.config import Settings
from app.core.enums import RiskScope, ScanStatus, TargetType
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
    """A fake at the real Module 07 AI Manager interface boundary. The
    Reporting Engine itself never touches this — it is used only to
    prepare a genuine, validated AIRecommendation fixture via the actual
    Module 07 service, exactly as production code would.
    """

    def resolve_provider_name(self):
        return "openrouter"

    def resolve_model_name(self):
        return "fake-integration-model"

    def generate(self, prompt):
        content = (
            '{"summary": "Upgrade the vulnerable OpenSSH service.", '
            '"explanation": "The detected version is affected by known CVEs.", '
            '"remediation_steps": ["Apply the latest OpenSSH security patch."], '
            '"validation_steps": ["Confirm the updated version via banner grab."], '
            '"cautions": ["Restart sshd during a maintenance window."]}'
        )
        return AIProviderResponse(
            content=content, provider="openrouter", model="fake-integration-model"
        )


def test_module05_through_module08_end_to_end(client: TestClient, db_session, tmp_path):
    # --- Module 05: persist an assessment package via InventoryService ---
    target = Target(target="203.0.113.60", target_type=TargetType.IPV4)
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
    vuln = ParsedVulnerability(
        name="Outdated OpenSSH",
        severity_score=8.2,
        severity_rating="High",
        cve="CVE-2024-9200",
    )
    service = ParsedService(
        port=22,
        protocol="tcp",
        service_name="ssh",
        product="OpenSSH",
        version="7.4",
        vulnerabilities=[vuln],
    )
    host = ParsedHost(
        ipv4="203.0.113.60", hostname="integration-host", services=[service]
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
    assert scan_risk.risk_score == 8.2

    # --- Module 07: generate a validated AI recommendation via the real provider ---
    vulnerability_risk = risk_repository.get_by_scan_and_scope(
        scan_job.id, RiskScope.VULNERABILITY
    )[0]
    ai_service = AIService(
        session=db_session,
        ai_recommendation_repository=AIRecommendationRepository(db_session),
        risk_repository=risk_repository,
        vulnerability_repository=VulnerabilityRepository(db_session),
        network_service_repository=NetworkServiceRepository(db_session),
        audit_service=audit_service,
        ai_manager=_FakeProviderBoundaryManager(),
    )
    ai_service.generate_recommendation(vulnerability_risk.id)

    # --- Module 08: generate the report through the real REST API ---
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
            ai_recommendation_repository=AIRecommendationRepository(db_session),
            audit_service=audit_service,
            settings=Settings(_env_file=None, report_output_directory=str(tmp_path)),
        )

    app.dependency_overrides[get_report_service] = override_report_service
    try:
        generate_response = client.post(
            "/api/v1/reports", json={"scan_id": str(scan_job.id)}
        )
        assert generate_response.status_code == 201
        report_data = generate_response.json()["data"]
        assert report_data["overall_risk_score"] == 8.2
        assert report_data["ai_recommendations_included"] == 1
        report_id = report_data["id"]

        # --- Report API retrieval ---
        get_response = client.get(f"/api/v1/reports/{report_id}")
        assert get_response.status_code == 200

        # --- PDF download ---
        download_response = client.get(f"/api/v1/reports/{report_id}/download")
        assert download_response.status_code == 200
        assert download_response.content[:5] == b"%PDF-"
        assert len(download_response.content) > 0
    finally:
        app.dependency_overrides.pop(get_report_service, None)

    # --- Module 06 remains authoritative: risk fields untouched by reporting ---
    db_session.refresh(scan_risk)
    assert scan_risk.risk_score == 8.2
