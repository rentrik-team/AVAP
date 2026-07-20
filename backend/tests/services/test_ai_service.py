import json
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.ai.manager import AIManager
from app.ai.provider import AIProviderResponse
from app.core.enums import RiskLevel, RiskScope, ScanStatus, TargetType
from app.core.exceptions import (
    AIProviderException,
    InsufficientContextException,
    InvalidAIResponseException,
    NotFoundException,
)
from app.models.ai_recommendation import AIRecommendation
from app.models.asset import Asset
from app.models.risk_assessment import RiskAssessment
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.models.vulnerability import Vulnerability
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.network_service_repository import NetworkServiceRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.ai_service import AIService
from app.services.audit_service import AuditService

VALID_OUTPUT = {
    "summary": "Outdated OpenSSH exposes known vulnerabilities.",
    "explanation": "The detected OpenSSH version is affected by known CVEs.",
    "remediation_steps": ["Upgrade OpenSSH to the latest stable release."],
    "validation_steps": ["Re-scan and confirm the version banner updated."],
    "cautions": ["Schedule during a maintenance window."],
}


class FakeAIManager(AIManager):
    """Test double at the AI Manager boundary — not a mock of AIService itself."""

    def __init__(
        self, content=None, provider="openrouter", model="fake-model", exc=None
    ):
        self.content = content if content is not None else json.dumps(VALID_OUTPUT)
        self.provider = provider
        self.model = model
        self.exc = exc
        self.generate_calls = []

    def resolve_provider_name(self):
        return self.provider

    def resolve_model_name(self):
        return self.model

    def generate(self, prompt):
        self.generate_calls.append(prompt)
        if self.exc:
            raise self.exc
        return AIProviderResponse(
            content=self.content, provider=self.provider, model=self.model
        )


@pytest.fixture
def vulnerability(db_session):
    v = Vulnerability(
        name="Outdated OpenSSH", severity_score=7.5, severity_rating="High"
    )
    db_session.add(v)
    db_session.flush()
    return v


@pytest.fixture
def target(db_session):
    t = Target(target="10.40.0.1", target_type=TargetType.IPV4)
    db_session.add(t)
    db_session.flush()
    return t


@pytest.fixture
def scan_job(db_session, target):
    job = ScanJob(target_id=target.id, status=ScanStatus.COMPLETED, scan_type="full")
    db_session.add(job)
    db_session.flush()
    return job


@pytest.fixture
def asset(db_session):
    a = Asset(ipv4="10.40.0.1")
    db_session.add(a)
    db_session.flush()
    return a


def _make_risk_assessment(
    db_session,
    scan_job,
    asset,
    vulnerability,
    scope=RiskScope.VULNERABILITY,
    calculated_at=None,
):
    ra = RiskAssessment(
        scope=scope,
        risk_score=7.5,
        risk_level=RiskLevel.HIGH,
        calculation_version="1.0.0",
        calculated_at=calculated_at or datetime.now(UTC),
        supporting_factors={},
        scan_id=scan_job.id,
        asset_id=(
            asset.id if scope in (RiskScope.VULNERABILITY, RiskScope.ASSET) else None
        ),
        vulnerability_id=vulnerability.id if scope == RiskScope.VULNERABILITY else None,
    )
    db_session.add(ra)
    db_session.flush()
    return ra


def _service(db_session, ai_manager=None):
    return AIService(
        session=db_session,
        ai_recommendation_repository=AIRecommendationRepository(db_session),
        risk_repository=RiskRepository(db_session),
        vulnerability_repository=VulnerabilityRepository(db_session),
        network_service_repository=NetworkServiceRepository(db_session),
        audit_service=AuditService(AuditRepository(db_session)),
        ai_manager=ai_manager or FakeAIManager(),
    )


# --- Not found / insufficient context ---


def test_generate_missing_risk_assessment_raises(db_session):
    service = _service(db_session)
    with pytest.raises(NotFoundException):
        service.generate_recommendation(uuid.uuid4())


def test_generate_insufficient_context_for_non_vulnerability_scope(
    db_session, scan_job, asset, vulnerability
):
    ra = _make_risk_assessment(
        db_session, scan_job, asset, vulnerability, scope=RiskScope.SCAN
    )
    service = _service(db_session)
    with pytest.raises(InsufficientContextException):
        service.generate_recommendation(ra.id)


def test_get_recommendation_not_found_raises(db_session):
    service = _service(db_session)
    with pytest.raises(NotFoundException):
        service.get_recommendation(uuid.uuid4())


# --- Successful generation and persistence ---


def test_generate_recommendation_persists_valid_output(
    db_session, scan_job, asset, vulnerability
):
    ra = _make_risk_assessment(db_session, scan_job, asset, vulnerability)
    manager = FakeAIManager()
    service = _service(db_session, ai_manager=manager)

    record = service.generate_recommendation(ra.id)

    assert record.vulnerability_id == vulnerability.id
    assert record.risk_assessment_id == ra.id
    assert record.summary == VALID_OUTPUT["summary"]
    assert record.remediation_steps == VALID_OUTPUT["remediation_steps"]
    assert len(manager.generate_calls) == 1


def test_get_recommendation_returns_persisted_record(
    db_session, scan_job, asset, vulnerability
):
    ra = _make_risk_assessment(db_session, scan_job, asset, vulnerability)
    service = _service(db_session)
    generated = service.generate_recommendation(ra.id)

    fetched = service.get_recommendation(ra.id)
    assert fetched.id == generated.id


# --- Idempotent regeneration behavior ---


def test_regeneration_with_unchanged_context_returns_existing_without_calling_provider(
    db_session, scan_job, asset, vulnerability
):
    ra = _make_risk_assessment(db_session, scan_job, asset, vulnerability)
    manager = FakeAIManager()
    service = _service(db_session, ai_manager=manager)

    first = service.generate_recommendation(ra.id)
    second = service.generate_recommendation(ra.id)

    assert second.id == first.id
    assert len(manager.generate_calls) == 1  # provider was not called again


def test_regeneration_after_risk_recalculation_calls_provider_again(
    db_session, scan_job, asset, vulnerability
):
    past = datetime.now(UTC) - timedelta(days=1)
    ra = _make_risk_assessment(
        db_session, scan_job, asset, vulnerability, calculated_at=past
    )
    manager = FakeAIManager()
    service = _service(db_session, ai_manager=manager)
    first = service.generate_recommendation(ra.id)

    # Simulate Module 06 recalculating this risk assessment more recently.
    # A explicit forward offset avoids flakiness from coarse OS clock
    # resolution making two back-to-back datetime.now() calls compare equal.
    ra.calculated_at = first.generated_at + timedelta(seconds=1)
    db_session.commit()

    second = service.generate_recommendation(ra.id)

    assert second.id == first.id  # same identity, updated in place
    assert len(manager.generate_calls) == 2


def test_different_model_creates_a_new_recommendation_identity(
    db_session, scan_job, asset, vulnerability
):
    ra = _make_risk_assessment(db_session, scan_job, asset, vulnerability)
    first_manager = FakeAIManager(model="model-a")
    first = _service(db_session, ai_manager=first_manager).generate_recommendation(
        ra.id
    )

    second_manager = FakeAIManager(model="model-b")
    second = _service(db_session, ai_manager=second_manager).generate_recommendation(
        ra.id
    )

    assert second.id != first.id


# --- Provider / validation failures ---


def test_generate_provider_failure_propagates_and_persists_nothing(
    db_session, scan_job, asset, vulnerability
):
    ra = _make_risk_assessment(db_session, scan_job, asset, vulnerability)
    manager = FakeAIManager(exc=AIProviderException("provider unavailable"))
    service = _service(db_session, ai_manager=manager)

    with pytest.raises(AIProviderException):
        service.generate_recommendation(ra.id)

    remaining = (
        db_session.query(AIRecommendation)
        .filter(AIRecommendation.risk_assessment_id == ra.id)
        .count()
    )
    assert remaining == 0


def test_generate_invalid_ai_output_not_persisted(
    db_session, scan_job, asset, vulnerability
):
    ra = _make_risk_assessment(db_session, scan_job, asset, vulnerability)
    manager = FakeAIManager(content="not valid json at all")
    service = _service(db_session, ai_manager=manager)

    with pytest.raises(InvalidAIResponseException):
        service.generate_recommendation(ra.id)

    remaining = (
        db_session.query(AIRecommendation)
        .filter(AIRecommendation.risk_assessment_id == ra.id)
        .count()
    )
    assert remaining == 0


def test_previous_valid_recommendation_preserved_after_regeneration_failure(
    db_session, scan_job, asset, vulnerability
):
    past = datetime.now(UTC) - timedelta(days=1)
    ra = _make_risk_assessment(
        db_session, scan_job, asset, vulnerability, calculated_at=past
    )
    good_manager = FakeAIManager()
    baseline = _service(db_session, ai_manager=good_manager).generate_recommendation(
        ra.id
    )
    assert baseline.summary == VALID_OUTPUT["summary"]

    # Force regeneration by advancing the risk assessment's calculation time.
    # A explicit forward offset avoids flakiness from coarse OS clock
    # resolution making two back-to-back datetime.now() calls compare equal.
    ra.calculated_at = baseline.generated_at + timedelta(seconds=1)
    db_session.commit()

    failing_manager = FakeAIManager(exc=AIProviderException("provider down"))
    with pytest.raises(AIProviderException):
        _service(db_session, ai_manager=failing_manager).generate_recommendation(ra.id)

    preserved = (
        db_session.query(AIRecommendation)
        .filter(AIRecommendation.risk_assessment_id == ra.id)
        .one()
    )
    assert preserved.id == baseline.id
    assert preserved.summary == VALID_OUTPUT["summary"]


def test_transaction_rollback_on_persistence_failure(
    db_session, scan_job, asset, vulnerability
):
    ra = _make_risk_assessment(db_session, scan_job, asset, vulnerability)
    service = _service(db_session)

    with (
        patch.object(
            service.ai_recommendation_repository,
            "upsert",
            side_effect=RuntimeError("db failure"),
        ),
        pytest.raises(RuntimeError),
    ):
        service.generate_recommendation(ra.id)

    remaining = (
        db_session.query(AIRecommendation)
        .filter(AIRecommendation.risk_assessment_id == ra.id)
        .count()
    )
    assert remaining == 0
