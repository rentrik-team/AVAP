from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.enums import RiskScope, ScanStatus, TargetType
from app.models.asset import Asset
from app.models.risk_assessment import RiskAssessment
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.models.vulnerability import Vulnerability


@pytest.fixture
def populated_state(db_session):
    target = Target(target="10.50.0.1", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()

    scan_job = ScanJob(
        target_id=target.id, status=ScanStatus.COMPLETED, scan_type="full"
    )
    db_session.add(scan_job)
    db_session.flush()

    asset = Asset(ipv4="10.50.0.1")
    db_session.add(asset)
    db_session.flush()

    vulnerability = Vulnerability(
        name="Dashboard API Test Vuln", severity_score=7.2, severity_rating="High"
    )
    db_session.add(vulnerability)
    db_session.flush()

    asset_risk = RiskAssessment(
        scope=RiskScope.ASSET,
        risk_score=7.0,
        risk_level="HIGH",
        calculation_version="1.0.0",
        calculated_at=datetime.now(UTC),
        supporting_factors={},
        scan_id=scan_job.id,
        asset_id=asset.id,
    )
    db_session.add(asset_risk)
    db_session.flush()

    return {"scan_job": scan_job, "asset": asset, "vulnerability": vulnerability}


# --- Empty dashboard: valid, not 404 ---


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/dashboard/summary",
        "/api/v1/dashboard/assets",
        "/api/v1/dashboard/vulnerabilities",
        "/api/v1/dashboard/risk",
        "/api/v1/dashboard/scans",
        "/api/v1/dashboard/reports",
        "/api/v1/dashboard/ai",
    ],
)
def test_empty_dashboard_endpoints_return_200(client: TestClient, path):
    response = client.get(path)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert "data" in body


def test_summary_populated_reflects_persisted_state(
    client: TestClient, populated_state
):
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_targets"] == 1
    assert data["total_scans"] == 1
    assert data["total_assets"] == 1
    assert data["unique_vulnerability_count"] == 1
    assert data["high_risk_asset_count"] == 1


def test_risk_endpoint_returns_top_risk_assets(client: TestClient, populated_state):
    response = client.get("/api/v1/dashboard/risk")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["top_risk_assets"]) == 1
    assert data["top_risk_assets"][0]["risk_score"] == 7.0


# --- Limit validation ---


def test_valid_limit_accepted(client: TestClient):
    response = client.get("/api/v1/dashboard/scans", params={"limit": 5})
    assert response.status_code == 200


def test_limit_below_minimum_rejected(client: TestClient):
    response = client.get("/api/v1/dashboard/scans", params={"limit": 0})
    assert response.status_code == 422


def test_limit_above_maximum_rejected(client: TestClient):
    response = client.get("/api/v1/dashboard/scans", params={"limit": 51})
    assert response.status_code == 422


def test_top_limit_above_maximum_rejected_on_risk_endpoint(client: TestClient):
    response = client.get("/api/v1/dashboard/risk", params={"top_limit": 1000})
    assert response.status_code == 422


def test_malformed_limit_query_parameter_rejected(client: TestClient):
    response = client.get("/api/v1/dashboard/scans", params={"limit": "not-a-number"})
    assert response.status_code == 422


# --- Security: no internal detail exposure ---


def test_response_never_exposes_internal_paths_or_secrets(
    client: TestClient, populated_state
):
    response = client.get("/api/v1/dashboard/reports")
    body = response.text.lower()
    assert "c:\\" not in body
    assert "/users/" not in body
    assert "api_key" not in body
    assert "password" not in body
    assert "database_url" not in body


def test_sql_injection_like_limit_payload_rejected(client: TestClient):
    response = client.get(
        "/api/v1/dashboard/scans", params={"limit": "1; DROP TABLE scan_jobs;--"}
    )
    assert response.status_code == 422


def test_sql_injection_like_scan_id_type_does_not_apply_here(client: TestClient):
    # Dashboard endpoints accept no client-supplied identifiers/paths at all;
    # confirm arbitrary query parameters are simply ignored, not interpreted.
    response = client.get(
        "/api/v1/dashboard/summary", params={"filter": "'; DROP TABLE targets; --"}
    )
    assert response.status_code == 200


# --- GET-only: dashboard never mutates ---


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/dashboard/summary",
        "/api/v1/dashboard/assets",
        "/api/v1/dashboard/risk",
    ],
)
def test_dashboard_endpoints_reject_post(client: TestClient, path):
    response = client.post(path, json={})
    assert response.status_code == 405


def test_dashboard_endpoints_do_not_create_any_scan(client: TestClient):
    before = client.get("/api/v1/dashboard/summary").json()["data"]["total_scans"]
    client.get("/api/v1/dashboard/scans")
    client.get("/api/v1/dashboard/risk")
    after = client.get("/api/v1/dashboard/summary").json()["data"]["total_scans"]
    assert before == after == 0
