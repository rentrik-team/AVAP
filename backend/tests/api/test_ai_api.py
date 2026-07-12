import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.ai.manager import AIManager
from app.api.routes.v1.ai import get_ai_service
from app.core.enums import RiskLevel, RiskScope, ScanStatus, TargetType
from app.main import app
from app.models.asset import Asset
from app.models.risk_assessment import RiskAssessment
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.models.vulnerability import Vulnerability
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.network_service_repository import NetworkServiceRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.ai_service import AIService
from tests.services.test_ai_service import FakeAIManager


@pytest.fixture(autouse=True)
def override_ai_service(db_session):
    def mock_get_ai_service():
        return AIService(
            session=db_session,
            ai_recommendation_repository=AIRecommendationRepository(db_session),
            risk_repository=RiskRepository(db_session),
            vulnerability_repository=VulnerabilityRepository(db_session),
            network_service_repository=NetworkServiceRepository(db_session),
            ai_manager=FakeAIManager(),
        )

    app.dependency_overrides[get_ai_service] = mock_get_ai_service
    yield
    app.dependency_overrides.pop(get_ai_service, None)


@pytest.fixture
def vulnerability_risk_assessment(db_session):
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
        name="API Test Vuln", severity_score=7.5, severity_rating="High"
    )
    db_session.add(vulnerability)
    db_session.flush()

    ra = RiskAssessment(
        scope=RiskScope.VULNERABILITY,
        risk_score=7.5,
        risk_level=RiskLevel.HIGH,
        calculation_version="1.0.0",
        calculated_at=datetime.now(UTC),
        supporting_factors={},
        scan_id=scan_job.id,
        asset_id=asset.id,
        vulnerability_id=vulnerability.id,
    )
    db_session.add(ra)
    db_session.flush()
    return ra


# --- Generate ---


def test_generate_recommendation(client: TestClient, vulnerability_risk_assessment):
    response = client.post(
        f"/api/v1/ai/recommendations/{vulnerability_risk_assessment.id}/generate"
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["risk_assessment_id"] == str(vulnerability_risk_assessment.id)
    assert data["summary"]
    assert isinstance(data["remediation_steps"], list)


def test_generate_recommendation_missing_risk_assessment(client: TestClient):
    response = client.post(f"/api/v1/ai/recommendations/{uuid.uuid4()}/generate")
    assert response.status_code == 404


def test_generate_recommendation_invalid_uuid(client: TestClient):
    response = client.post("/api/v1/ai/recommendations/not-a-uuid/generate")
    assert response.status_code == 422


def test_generate_recommendation_is_callable_repeatedly(
    client: TestClient, vulnerability_risk_assessment
):
    url = f"/api/v1/ai/recommendations/{vulnerability_risk_assessment.id}/generate"
    first = client.post(url).json()["data"]
    second = client.post(url).json()["data"]
    assert first["id"] == second["id"]


# --- Retrieve ---


def test_get_recommendation_not_generated_yet(
    client: TestClient, vulnerability_risk_assessment
):
    response = client.get(
        f"/api/v1/ai/recommendations/{vulnerability_risk_assessment.id}"
    )
    assert response.status_code == 404


def test_get_recommendation_after_generation(
    client: TestClient, vulnerability_risk_assessment
):
    client.post(
        f"/api/v1/ai/recommendations/{vulnerability_risk_assessment.id}/generate"
    )
    response = client.get(
        f"/api/v1/ai/recommendations/{vulnerability_risk_assessment.id}"
    )
    assert response.status_code == 200
    assert response.json()["data"]["summary"]


def test_get_recommendation_invalid_uuid(client: TestClient):
    response = client.get("/api/v1/ai/recommendations/not-a-uuid")
    assert response.status_code == 422


# --- Providers / Models (no DB dependency, real AIManager against test settings) ---


def test_list_providers(client: TestClient):
    response = client.get("/api/v1/ai/providers")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "openrouter" in data["supported_providers"]
    assert data["active_provider"] == AIManager().resolve_provider_name()


def test_get_model_info(client: TestClient):
    response = client.get("/api/v1/ai/models")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["provider"] == "openrouter"
    assert data["model"]


# --- Security: sanitization ---


def test_generate_recommendation_provider_failure_sanitized(
    client: TestClient, db_session, vulnerability_risk_assessment
):
    from app.core.exceptions import AIProviderException

    def failing_ai_service():
        return AIService(
            session=db_session,
            ai_recommendation_repository=AIRecommendationRepository(db_session),
            risk_repository=RiskRepository(db_session),
            vulnerability_repository=VulnerabilityRepository(db_session),
            network_service_repository=NetworkServiceRepository(db_session),
            ai_manager=FakeAIManager(
                exc=AIProviderException("AI provider returned an error status: 401.")
            ),
        )

    app.dependency_overrides[get_ai_service] = failing_ai_service
    response = client.post(
        f"/api/v1/ai/recommendations/{vulnerability_risk_assessment.id}/generate"
    )
    assert response.status_code == 502
    body = response.json()
    assert body["success"] is False
    # The sanitized provider-boundary exception message never carries API
    # keys, authorization headers, or raw HTTP client internals.
    for leaked_marker in ("Authorization", "Bearer", "api_key", "Traceback", "httpx."):
        assert leaked_marker not in response.text


def test_generate_recommendation_invalid_output_sanitized(
    client: TestClient, db_session, vulnerability_risk_assessment
):
    def invalid_output_service():
        return AIService(
            session=db_session,
            ai_recommendation_repository=AIRecommendationRepository(db_session),
            risk_repository=RiskRepository(db_session),
            vulnerability_repository=VulnerabilityRepository(db_session),
            network_service_repository=NetworkServiceRepository(db_session),
            ai_manager=FakeAIManager(content="not valid json"),
        )

    app.dependency_overrides[get_ai_service] = invalid_output_service
    response = client.post(
        f"/api/v1/ai/recommendations/{vulnerability_risk_assessment.id}/generate"
    )
    assert response.status_code == 502
    assert response.json()["success"] is False
