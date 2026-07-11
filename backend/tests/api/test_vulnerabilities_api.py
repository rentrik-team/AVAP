import uuid
import pytest
from fastapi.testclient import TestClient

from app.models.vulnerability import Vulnerability


@pytest.fixture
def sample_vulnerabilities(db_session):
    """Create sample vulnerabilities for testing."""
    v1 = Vulnerability(
        name="SQL Injection",
        severity_score=9.8,
        severity_rating="Critical",
        description="SQL injection vulnerability",
        cve="CVE-2023-1111"
    )
    v2 = Vulnerability(
        name="Path Traversal",
        severity_score=7.5,
        severity_rating="High",
        description="Path traversal vulnerability",
        cve="CVE-2023-2222"
    )
    v3 = Vulnerability(
        name="Weak Cipher",
        severity_score=3.0,
        severity_rating="Low",
        description="Weak cipher detected",
        cve=None
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

def test_list_vulnerabilities_rating_filtering(client: TestClient, sample_vulnerabilities):
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
