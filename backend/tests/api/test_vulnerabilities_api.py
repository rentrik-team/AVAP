import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.enums import ScanStatus, TargetType
from app.models.asset import Asset
from app.models.scan_finding import ScanFinding
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.models.vulnerability import Vulnerability


@pytest.fixture
def sample_vulnerabilities(db_session):
    """Create sample vulnerabilities for testing."""
    v1 = Vulnerability(
        name="SQL Injection",
        severity_score=9.8,
        severity_rating="Critical",
        description="SQL injection vulnerability",
        cve="CVE-2023-1111",
    )
    v2 = Vulnerability(
        name="Path Traversal",
        severity_score=7.5,
        severity_rating="High",
        description="Path traversal vulnerability",
        cve="CVE-2023-2222",
    )
    v3 = Vulnerability(
        name="Weak Cipher",
        severity_score=3.0,
        severity_rating="Low",
        description="Weak cipher detected",
        cve=None,
    )
    db_session.add_all([v1, v2, v3])
    db_session.flush()
    return {"v1": v1, "v2": v2, "v3": v3}


# --- List ---


def test_list_vulnerabilities(client: TestClient, sample_vulnerabilities):
    response = client.get("/api/v1/vulnerabilities/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 3
    assert len(data["data"]["vulnerabilities"]) == 3


def test_list_vulnerabilities_pagination(client: TestClient, sample_vulnerabilities):
    response = client.get("/api/v1/vulnerabilities/?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 3
    assert len(data["data"]["vulnerabilities"]) == 2


# --- Filters ---


def test_list_vulnerabilities_rating_filtering(
    client: TestClient, sample_vulnerabilities
):
    response = client.get("/api/v1/vulnerabilities/?severity_rating=high")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["vulnerabilities"][0]["name"] == "Path Traversal"


def test_list_vulnerabilities_cve_filtering(client: TestClient, sample_vulnerabilities):
    response = client.get("/api/v1/vulnerabilities/?cve=CVE-2023-1111")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["vulnerabilities"][0]["name"] == "SQL Injection"


def test_list_vulnerabilities_scan_id_filtering(
    client: TestClient, db_session, sample_vulnerabilities
):
    """scan_id scopes the list to findings linked to that one scan — the
    Scan Detail page's Security Analysis section depends on this."""
    target = Target(target="10.0.3.1", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()

    scan = ScanJob(target_id=target.id, scan_type="full", status=ScanStatus.COMPLETED)
    asset = Asset(ipv4="10.0.3.1")
    db_session.add_all([scan, asset])
    db_session.flush()

    db_session.add(
        ScanFinding(
            scan_id=scan.id,
            asset_id=asset.id,
            vulnerability_id=sample_vulnerabilities["v1"].id,
        )
    )
    db_session.flush()

    response = client.get(f"/api/v1/vulnerabilities/?scan_id={scan.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["vulnerabilities"][0]["name"] == "SQL Injection"

    # A scan with no findings returns an empty, well-formed list.
    other_scan = ScanJob(
        target_id=target.id, scan_type="full", status=ScanStatus.COMPLETED
    )
    db_session.add(other_scan)
    db_session.flush()
    response = client.get(f"/api/v1/vulnerabilities/?scan_id={other_scan.id}")
    assert response.status_code == 200
    assert response.json()["data"]["total"] == 0


# --- Detail ---


def test_get_vulnerability_detail(client: TestClient, sample_vulnerabilities):
    vuln_id = sample_vulnerabilities["v1"].id
    response = client.get(f"/api/v1/vulnerabilities/{vuln_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == str(vuln_id)
    assert data["data"]["name"] == "SQL Injection"
    assert data["data"]["severity_score"] == 9.8


def test_get_vulnerability_not_found(client: TestClient):
    response = client.get(f"/api/v1/vulnerabilities/{uuid.uuid4()}")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
