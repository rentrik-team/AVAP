"""End-to-end integration: Module 05 persisted findings -> Module 06 risk
calculation -> persisted risk assessments -> Risk API retrieval.
"""

from fastapi.testclient import TestClient

from app.core.enums import ScanStatus, TargetType
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.parsers.models import (
    AssessmentPackage,
    ParsedHost,
    ParsedService,
    ParsedVulnerability,
)
from app.repositories.asset_repository import AssetRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.inventory_service import InventoryService
from app.services.risk_service import RiskService


def test_module05_findings_flow_into_module06_risk_and_api(
    client: TestClient, db_session
):
    # --- Module 05: persist an assessment package via InventoryService ---
    target = Target(target="203.0.113.5", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()

    scan_job = ScanJob(target_id=target.id, status=ScanStatus.RUNNING, scan_type="full")
    db_session.add(scan_job)
    db_session.flush()

    inventory_service = InventoryService(
        db_session,
        AssetRepository(db_session),
        VulnerabilityRepository(db_session),
        ScanRepository(db_session),
    )

    high_vuln = ParsedVulnerability(
        name="Outdated TLS",
        severity_score=8.1,
        severity_rating="High",
        cve="CVE-2024-9001",
    )
    critical_vuln = ParsedVulnerability(
        name="Remote Code Execution",
        severity_score=9.8,
        severity_rating="Critical",
        cve="CVE-2024-9002",
    )
    service_a = ParsedService(
        port=443, protocol="tcp", service_name="https", vulnerabilities=[high_vuln]
    )
    service_b = ParsedService(
        port=22, protocol="tcp", service_name="ssh", vulnerabilities=[critical_vuln]
    )
    host = ParsedHost(ipv4="203.0.113.5", services=[service_a, service_b])

    package = AssessmentPackage(
        scan_id=scan_job.id, scanner_type="OPENVAS", parsed_hosts=[host]
    )
    inventory_service.process_assessment_package(package)

    # --- Module 06: calculate deterministic risk from the persisted findings ---
    risk_service = RiskService(
        session=db_session,
        risk_repository=RiskRepository(db_session),
        scan_repository=ScanRepository(db_session),
        asset_repository=AssetRepository(db_session),
        scan_finding_repository=ScanFindingRepository(db_session),
    )
    scan_risk = risk_service.calculate_risk_for_scan(scan_job.id)

    # Worst finding (CVSS 9.8, Critical) drives the scan-level risk.
    assert scan_risk.risk_score == 9.8
    assert scan_risk.risk_level.value == "CRITICAL"

    # --- Risk API retrieval ---
    scan_response = client.get(f"/api/v1/risk/scans/{scan_job.id}")
    assert scan_response.status_code == 200
    assert scan_response.json()["data"]["risk_score"] == 9.8

    summary_response = client.get("/api/v1/risk/summary")
    assert summary_response.status_code == 200
    assert summary_response.json()["data"]["risk_score"] == 9.8

    list_response = client.get("/api/v1/risk?scope=VULNERABILITY")
    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 2
