from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.enums import RiskLevel, RiskScope, ScanStatus, TargetType
from app.models.asset import Asset
from app.models.risk_assessment import RiskAssessment
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.repositories.risk_repository import RiskRepository


@pytest.fixture
def target(db_session):
    t = Target(target="10.10.10.1", target_type=TargetType.IPV4)
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
    a = Asset(ipv4="10.10.10.1")
    db_session.add(a)
    db_session.flush()
    return a


@pytest.fixture
def risk_repository(db_session):
    return RiskRepository(db_session)


def _now():
    return datetime.now(UTC)


# --- Upsert: first calculation ---


def test_upsert_creates_new_record(risk_repository, scan_job, asset):
    record = risk_repository.upsert(
        scope=RiskScope.ASSET,
        risk_score=5.0,
        risk_level=RiskLevel.MEDIUM,
        calculation_version="1.0.0",
        calculated_at=_now(),
        supporting_factors={"aggregation_method": "maximum"},
        scan_id=scan_job.id,
        asset_id=asset.id,
    )
    assert record.id is not None
    assert record.risk_score == 5.0


# --- Upsert: repeated calculation updates in place (idempotent) ---


def test_upsert_updates_existing_record_in_place(
    db_session, risk_repository, scan_job, asset
):
    first = risk_repository.upsert(
        scope=RiskScope.ASSET,
        risk_score=5.0,
        risk_level=RiskLevel.MEDIUM,
        calculation_version="1.0.0",
        calculated_at=_now(),
        supporting_factors={},
        scan_id=scan_job.id,
        asset_id=asset.id,
    )
    first_id = first.id

    second = risk_repository.upsert(
        scope=RiskScope.ASSET,
        risk_score=8.0,
        risk_level=RiskLevel.HIGH,
        calculation_version="1.0.0",
        calculated_at=_now(),
        supporting_factors={"changed": True},
        scan_id=scan_job.id,
        asset_id=asset.id,
    )

    assert second.id == first_id
    assert second.risk_score == 8.0
    assert second.risk_level == RiskLevel.HIGH

    count = (
        db_session.query(RiskAssessment)
        .filter(
            RiskAssessment.scope == RiskScope.ASSET, RiskAssessment.asset_id == asset.id
        )
        .count()
    )
    assert count == 1


# --- Database constraint: scope invariants enforced ---


def test_scope_invariant_check_constraint_rejects_invalid_combination(
    db_session, scan_job, asset
):
    """A SCAN-scope row must not carry an asset_id; the CHECK constraint rejects it."""
    invalid = RiskAssessment(
        scope=RiskScope.SCAN,
        risk_score=1.0,
        risk_level=RiskLevel.LOW,
        calculation_version="1.0.0",
        calculated_at=_now(),
        supporting_factors={},
        scan_id=scan_job.id,
        asset_id=asset.id,  # invalid: SCAN scope forbids asset_id
    )
    db_session.add(invalid)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_duplicate_scope_entity_rejected_by_unique_constraint(db_session, scan_job):
    """The partial unique index, not application logic, is the source of truth here."""
    first = RiskAssessment(
        scope=RiskScope.SCAN,
        risk_score=1.0,
        risk_level=RiskLevel.LOW,
        calculation_version="1.0.0",
        calculated_at=_now(),
        supporting_factors={},
        scan_id=scan_job.id,
    )
    db_session.add(first)
    db_session.flush()

    duplicate = RiskAssessment(
        scope=RiskScope.SCAN,
        risk_score=2.0,
        risk_level=RiskLevel.LOW,
        calculation_version="1.0.0",
        calculated_at=_now(),
        supporting_factors={},
        scan_id=scan_job.id,
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# --- Repository never commits ---


def test_upsert_does_not_commit(db_session, risk_repository, scan_job):
    risk_repository.upsert(
        scope=RiskScope.SCAN,
        risk_score=3.0,
        risk_level=RiskLevel.LOW,
        calculation_version="1.0.0",
        calculated_at=_now(),
        supporting_factors={},
        scan_id=scan_job.id,
    )
    # Rolling back must undo the write, proving the repository only flushed.
    db_session.rollback()
    remaining = (
        db_session.query(RiskAssessment)
        .filter(RiskAssessment.scan_id == scan_job.id)
        .count()
    )
    assert remaining == 0


# --- Read methods ---


def test_get_all_filters_by_scope_and_level(risk_repository, scan_job, asset):
    risk_repository.upsert(
        scope=RiskScope.SCAN,
        risk_score=9.5,
        risk_level=RiskLevel.CRITICAL,
        calculation_version="1.0.0",
        calculated_at=_now(),
        supporting_factors={},
        scan_id=scan_job.id,
    )
    risk_repository.upsert(
        scope=RiskScope.ASSET,
        risk_score=2.0,
        risk_level=RiskLevel.LOW,
        calculation_version="1.0.0",
        calculated_at=_now(),
        supporting_factors={},
        scan_id=scan_job.id,
        asset_id=asset.id,
    )

    scan_items, scan_total = risk_repository.get_all(scope=RiskScope.SCAN)
    assert scan_total == 1
    assert scan_items[0].scope == RiskScope.SCAN

    critical_items, critical_total = risk_repository.get_all(
        risk_level=RiskLevel.CRITICAL
    )
    assert critical_total == 1
    assert critical_items[0].risk_level == RiskLevel.CRITICAL


def test_get_by_asset_returns_only_asset_scope(risk_repository, scan_job, asset):
    risk_repository.upsert(
        scope=RiskScope.ASSET,
        risk_score=4.0,
        risk_level=RiskLevel.MEDIUM,
        calculation_version="1.0.0",
        calculated_at=_now(),
        supporting_factors={},
        scan_id=scan_job.id,
        asset_id=asset.id,
    )
    items, total = risk_repository.get_by_asset(asset.id)
    assert total == 1
    assert items[0].asset_id == asset.id


def test_get_by_scan_returns_singleton(risk_repository, scan_job):
    risk_repository.upsert(
        scope=RiskScope.SCAN,
        risk_score=6.0,
        risk_level=RiskLevel.MEDIUM,
        calculation_version="1.0.0",
        calculated_at=_now(),
        supporting_factors={},
        scan_id=scan_job.id,
    )
    record = risk_repository.get_by_scan(scan_job.id)
    assert record is not None
    assert record.scan_id == scan_job.id


def test_get_by_scan_returns_none_when_not_calculated(risk_repository, scan_job):
    assert risk_repository.get_by_scan(scan_job.id) is None


def test_get_assessment_returns_none_when_absent(risk_repository):
    assert risk_repository.get_assessment() is None


def test_get_all_scan_scores(risk_repository, scan_job):
    risk_repository.upsert(
        scope=RiskScope.SCAN,
        risk_score=7.0,
        risk_level=RiskLevel.HIGH,
        calculation_version="1.0.0",
        calculated_at=_now(),
        supporting_factors={},
        scan_id=scan_job.id,
    )
    scores = risk_repository.get_all_scan_scores()
    assert (scan_job.id, 7.0) in scores
