"""End-to-end integration: Module 05 persisted findings -> Module 06 risk
calculation -> Module 07 remediation context -> fake provider through the
provider interface -> validated structured recommendation -> persisted AI
recommendation -> AI API retrieval.
"""

from fastapi.testclient import TestClient

from app.ai.manager import AIManager
from app.ai.provider import AIProviderResponse
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
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.ai_service import AIService
from app.services.audit_service import AuditService
from app.services.inventory_service import InventoryService
from app.services.risk_service import RiskService


class _FakeProviderBoundaryManager(AIManager):
    """A fake positioned exactly at the AI Manager / provider interface
    boundary — the real AIManager contract, backed by a canned response
    instead of a live OpenRouter call.
    """

    def __init__(self):
        self.calls = 0

    def resolve_provider_name(self):
        return "openrouter"

    def resolve_model_name(self):
        return "fake-integration-model"

    def generate(self, prompt):
        self.calls += 1
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


def test_module05_through_module07_end_to_end(client: TestClient, db_session):
    # --- Module 05: persist an assessment package via InventoryService ---
    target = Target(target="203.0.113.9", target_type=TargetType.IPV4)
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
        severity_score=7.5,
        severity_rating="High",
        cve="CVE-2024-9100",
    )
    service = ParsedService(
        port=22,
        protocol="tcp",
        service_name="ssh",
        product="OpenSSH",
        version="7.4",
        vulnerabilities=[vuln],
    )
    host = ParsedHost(ipv4="203.0.113.9", services=[service])
    package = AssessmentPackage(
        scan_id=scan_job.id, scanner_type="OPENVAS", parsed_hosts=[host]
    )
    inventory_service.process_assessment_package(package)

    # --- Module 06: calculate deterministic risk ---
    risk_service = RiskService(
        session=db_session,
        risk_repository=RiskRepository(db_session),
        scan_repository=ScanRepository(db_session),
        asset_repository=AssetRepository(db_session),
        scan_finding_repository=ScanFindingRepository(db_session),
        audit_service=audit_service,
    )
    risk_service.calculate_risk_for_scan(scan_job.id)

    vulnerability_risk_assessments, total = risk_service.risk_repository.get_all(
        scope=RiskScope.VULNERABILITY
    )
    assert total == 1
    risk_assessment = vulnerability_risk_assessments[0]
    assert risk_assessment.risk_score == 7.5

    # --- Module 07: generate remediation through the fake provider boundary ---
    fake_manager = _FakeProviderBoundaryManager()
    ai_service = AIService(
        session=db_session,
        ai_recommendation_repository=AIRecommendationRepository(db_session),
        risk_repository=RiskRepository(db_session),
        vulnerability_repository=VulnerabilityRepository(db_session),
        network_service_repository=NetworkServiceRepository(db_session),
        audit_service=audit_service,
        ai_manager=fake_manager,
    )
    recommendation = ai_service.generate_recommendation(risk_assessment.id)

    assert recommendation.risk_assessment_id == risk_assessment.id
    assert recommendation.summary == "Upgrade the vulnerable OpenSSH service."
    assert fake_manager.calls == 1

    # --- AI API retrieval ---
    response = client.get(f"/api/v1/ai/recommendations/{risk_assessment.id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["remediation_steps"] == ["Apply the latest OpenSSH security patch."]

    # --- Module 06 remains authoritative: risk fields are untouched ---
    db_session.refresh(risk_assessment)
    assert risk_assessment.risk_score == 7.5
