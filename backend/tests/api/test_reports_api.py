import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes.v1.reports import get_report_service
from app.core.config import Settings
from app.core.enums import ScanStatus, TargetType
from app.main import app
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
from app.services.audit_service import AuditService
from app.services.inventory_service import InventoryService
from app.services.report_service import ReportService
from app.services.risk_service import RiskService


@pytest.fixture(autouse=True)
def override_report_service(db_session, tmp_path):
    def mock_get_report_service():
        return ReportService(
            session=db_session,
            report_repository=ReportRepository(db_session),
            scan_repository=ScanRepository(db_session),
            risk_repository=RiskRepository(db_session),
            asset_repository=AssetRepository(db_session),
            vulnerability_repository=VulnerabilityRepository(db_session),
            network_service_repository=NetworkServiceRepository(db_session),
            scan_finding_repository=ScanFindingRepository(db_session),
            ai_recommendation_repository=AIRecommendationRepository(db_session),
            audit_service=AuditService(AuditRepository(db_session)),
            settings=Settings(_env_file=None, report_output_directory=str(tmp_path)),
        )

    app.dependency_overrides[get_report_service] = mock_get_report_service
    yield
    app.dependency_overrides.pop(get_report_service, None)


@pytest.fixture
def scan_with_risk(db_session):
    target = Target(target="203.0.113.40", target_type=TargetType.IPV4)
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
        name="API Test Vuln", severity_score=8.5, severity_rating="High"
    )
    service = ParsedService(
        port=443, protocol="tcp", service_name="https", vulnerabilities=[vuln]
    )
    host = ParsedHost(ipv4="203.0.113.40", services=[service])
    package = AssessmentPackage(
        scan_id=scan_job.id, scanner_type="OPENVAS", parsed_hosts=[host]
    )
    inventory_service.process_assessment_package(package)

    risk_service = RiskService(
        session=db_session,
        risk_repository=RiskRepository(db_session),
        scan_repository=ScanRepository(db_session),
        asset_repository=AssetRepository(db_session),
        scan_finding_repository=ScanFindingRepository(db_session),
        audit_service=audit_service,
    )
    risk_service.calculate_risk_for_scan(scan_job.id)

    return scan_job


# --- Generate ---


def test_generate_report(client: TestClient, scan_with_risk):
    response = client.post("/api/v1/reports", json={"scan_id": str(scan_with_risk.id)})
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["scan_id"] == str(scan_with_risk.id)
    assert data["overall_risk_score"] == 8.5
    assert "id" in data


def test_generate_report_missing_scan(client: TestClient):
    response = client.post("/api/v1/reports", json={"scan_id": str(uuid.uuid4())})
    assert response.status_code == 404


def test_generate_report_invalid_uuid(client: TestClient):
    response = client.post("/api/v1/reports", json={"scan_id": "not-a-uuid"})
    assert response.status_code == 422


def test_generate_report_missing_risk_context(client: TestClient, db_session):
    target = Target(target="203.0.113.41", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()
    scan_job = ScanJob(target_id=target.id, status=ScanStatus.PENDING, scan_type="full")
    db_session.add(scan_job)
    db_session.flush()

    response = client.post("/api/v1/reports", json={"scan_id": str(scan_job.id)})
    assert response.status_code == 422


# --- Retrieve metadata ---


def test_get_report_metadata(client: TestClient, scan_with_risk):
    generate_response = client.post(
        "/api/v1/reports", json={"scan_id": str(scan_with_risk.id)}
    )
    report_id = generate_response.json()["data"]["id"]

    response = client.get(f"/api/v1/reports/{report_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == report_id


def test_get_report_not_found(client: TestClient):
    response = client.get(f"/api/v1/reports/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_report_invalid_uuid(client: TestClient):
    response = client.get("/api/v1/reports/not-a-uuid")
    assert response.status_code == 422


# --- List ---


def test_list_reports(client: TestClient, scan_with_risk):
    client.post("/api/v1/reports", json={"scan_id": str(scan_with_risk.id)})
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1


def test_list_reports_filtered_by_scan(client: TestClient, scan_with_risk):
    client.post("/api/v1/reports", json={"scan_id": str(scan_with_risk.id)})
    response = client.get(f"/api/v1/reports?scan_id={scan_with_risk.id}")
    assert response.status_code == 200
    assert response.json()["data"]["total"] == 1


def test_list_reports_empty(client: TestClient):
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    assert response.json()["data"]["total"] == 0


# --- Download ---


def test_download_report(client: TestClient, scan_with_risk):
    generate_response = client.post(
        "/api/v1/reports", json={"scan_id": str(scan_with_risk.id)}
    )
    report_id = generate_response.json()["data"]["id"]

    response = client.get(f"/api/v1/reports/{report_id}/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:5] == b"%PDF-"
    # No internal filesystem path is ever exposed to the client.
    assert "C:\\" not in response.headers.get("content-disposition", "")
    assert "/home/" not in response.headers.get("content-disposition", "")
    assert f"avap-report-{report_id}.pdf" in response.headers["content-disposition"]


def test_download_report_not_found(client: TestClient):
    response = client.get(f"/api/v1/reports/{uuid.uuid4()}/download")
    assert response.status_code == 404


def test_download_report_missing_physical_file(
    client: TestClient, scan_with_risk, tmp_path
):
    generate_response = client.post(
        "/api/v1/reports", json={"scan_id": str(scan_with_risk.id)}
    )
    data = generate_response.json()["data"]
    report_id = data["id"]

    # Simulate the file having disappeared from storage after generation.
    for pdf_file in Path(tmp_path).glob("*.pdf"):
        pdf_file.unlink()

    response = client.get(f"/api/v1/reports/{report_id}/download")
    assert response.status_code == 404


# --- Delete ---


def test_delete_report(client: TestClient, scan_with_risk):
    generate_response = client.post(
        "/api/v1/reports", json={"scan_id": str(scan_with_risk.id)}
    )
    report_id = generate_response.json()["data"]["id"]

    response = client.delete(f"/api/v1/reports/{report_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/reports/{report_id}")
    assert get_response.status_code == 404


def test_delete_report_not_found(client: TestClient):
    response = client.delete(f"/api/v1/reports/{uuid.uuid4()}")
    assert response.status_code == 404
