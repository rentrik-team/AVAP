import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.enums import RiskLevel, RiskScope, ScanStatus, TargetType
from app.models.ai_recommendation import AIRecommendation
from app.models.asset import Asset
from app.models.risk_assessment import RiskAssessment
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.models.vulnerability import Vulnerability
from app.repositories.ai_recommendation_repository import AIRecommendationRepository


@pytest.fixture
def vulnerability(db_session):
    v = Vulnerability(
        name="Outdated OpenSSH", severity_score=7.5, severity_rating="High"
    )
    db_session.add(v)
    db_session.flush()
    return v


@pytest.fixture
def risk_assessment(db_session, vulnerability):
    target = Target(target="10.30.0.1", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()

    scan_job = ScanJob(
        target_id=target.id, status=ScanStatus.COMPLETED, scan_type="full"
    )
    db_session.add(scan_job)
    db_session.flush()

    asset = Asset(ipv4="10.30.0.1")
    db_session.add(asset)
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


@pytest.fixture
def repository(db_session):
    return AIRecommendationRepository(db_session)


def _now():
    return datetime.now(UTC)


def _upsert_kwargs(vulnerability, risk_assessment, **overrides):
    defaults = {
        "vulnerability_id": vulnerability.id,
        "risk_assessment_id": risk_assessment.id,
        "provider": "openrouter",
        "model": "test-model",
        "prompt_version": "1.0.0",
        "summary": "Summary",
        "explanation": "Explanation",
        "remediation_steps": ["Do the thing"],
        "validation_steps": ["Verify the thing"],
        "cautions": ["Be careful"],
        "generated_at": _now(),
    }
    defaults.update(overrides)
    return defaults


# --- Create ---


def test_upsert_creates_new_recommendation(repository, vulnerability, risk_assessment):
    record = repository.upsert(**_upsert_kwargs(vulnerability, risk_assessment))
    assert record.id is not None
    assert record.summary == "Summary"


# --- Retrieve by ID ---


def test_get_by_id_returns_record(repository, vulnerability, risk_assessment):
    created = repository.upsert(**_upsert_kwargs(vulnerability, risk_assessment))
    fetched = repository.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id


def test_get_by_id_returns_none_when_absent(repository):
    assert repository.get_by_id(uuid.uuid4()) is None


# --- Retrieve by vulnerability ---


def test_get_by_vulnerability_returns_history(
    repository, vulnerability, risk_assessment
):
    repository.upsert(**_upsert_kwargs(vulnerability, risk_assessment))
    items, total = repository.get_by_vulnerability(vulnerability.id)
    assert total == 1
    assert items[0].vulnerability_id == vulnerability.id


def test_get_by_vulnerability_empty_when_none_generated(repository, vulnerability):
    items, total = repository.get_by_vulnerability(vulnerability.id)
    assert total == 0
    assert items == []


# --- Logical uniqueness / idempotent regeneration ---


def test_upsert_updates_existing_identity_in_place(
    db_session, repository, vulnerability, risk_assessment
):
    first = repository.upsert(
        **_upsert_kwargs(vulnerability, risk_assessment, summary="First")
    )
    second = repository.upsert(
        **_upsert_kwargs(vulnerability, risk_assessment, summary="Second")
    )

    assert second.id == first.id
    assert second.summary == "Second"

    count = (
        db_session.query(AIRecommendation)
        .filter(AIRecommendation.risk_assessment_id == risk_assessment.id)
        .count()
    )
    assert count == 1


def test_different_prompt_version_creates_new_record(
    repository, vulnerability, risk_assessment
):
    first = repository.upsert(
        **_upsert_kwargs(vulnerability, risk_assessment, prompt_version="1.0.0")
    )
    second = repository.upsert(
        **_upsert_kwargs(vulnerability, risk_assessment, prompt_version="2.0.0")
    )
    assert second.id != first.id


def test_different_model_creates_new_record(repository, vulnerability, risk_assessment):
    first = repository.upsert(
        **_upsert_kwargs(vulnerability, risk_assessment, model="model-a")
    )
    second = repository.upsert(
        **_upsert_kwargs(vulnerability, risk_assessment, model="model-b")
    )
    assert second.id != first.id


def test_duplicate_identity_rejected_by_unique_constraint(
    db_session, vulnerability, risk_assessment
):
    """The unique constraint, not application logic, is the source of truth here."""
    kwargs = _upsert_kwargs(vulnerability, risk_assessment)
    first = AIRecommendation(**kwargs)
    db_session.add(first)
    db_session.flush()

    duplicate = AIRecommendation(**kwargs)
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# --- Repository never commits ---


def test_upsert_does_not_commit(db_session, repository, vulnerability, risk_assessment):
    repository.upsert(**_upsert_kwargs(vulnerability, risk_assessment))
    db_session.rollback()
    remaining = (
        db_session.query(AIRecommendation)
        .filter(AIRecommendation.vulnerability_id == vulnerability.id)
        .count()
    )
    assert remaining == 0


# --- find_identity_record ---


def test_find_identity_record_matches_exact_combination(
    repository, vulnerability, risk_assessment
):
    repository.upsert(**_upsert_kwargs(vulnerability, risk_assessment))
    found = repository.find_identity_record(
        risk_assessment_id=risk_assessment.id,
        provider="openrouter",
        model="test-model",
        prompt_version="1.0.0",
    )
    assert found is not None


def test_find_identity_record_none_for_different_provider(
    repository, vulnerability, risk_assessment
):
    repository.upsert(**_upsert_kwargs(vulnerability, risk_assessment))
    found = repository.find_identity_record(
        risk_assessment_id=risk_assessment.id,
        provider="groq",
        model="test-model",
        prompt_version="1.0.0",
    )
    assert found is None
