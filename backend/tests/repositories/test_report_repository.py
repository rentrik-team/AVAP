import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.enums import RiskLevel, ScanStatus, TargetType
from app.models.report import Report
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.repositories.report_repository import ReportRepository


@pytest.fixture
def scan_job(db_session):
    target = Target(target="10.70.0.1", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()
    job = ScanJob(target_id=target.id, status=ScanStatus.COMPLETED, scan_type="full")
    db_session.add(job)
    db_session.flush()
    return job


@pytest.fixture
def repository(db_session):
    return ReportRepository(db_session)


def _report(scan_id, generated_at=None, **overrides):
    defaults = {
        "scan_id": scan_id,
        "format": "PDF",
        "report_template_version": "1.0.0",
        "risk_calculation_version": "1.0.0",
        "source_risk_calculated_at": datetime.now(UTC),
        "overall_risk_score": 7.5,
        "overall_risk_level": RiskLevel.HIGH,
        "vulnerability_count": 1,
        "ai_recommendations_included": 0,
        "file_name": f"report_{uuid.uuid4()}.pdf",
        "file_size_bytes": 1024,
        "generated_at": generated_at or datetime.now(UTC),
    }
    defaults.update(overrides)
    return Report(**defaults)


# --- Create / retrieve ---


def test_create_report(repository, scan_job):
    report = repository.create(_report(scan_job.id))
    assert report.id is not None
    assert report.scan_id == scan_job.id


def test_get_by_id_returns_report(repository, scan_job):
    created = repository.create(_report(scan_job.id))
    fetched = repository.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id


def test_get_by_id_returns_none_when_absent(repository):
    assert repository.get_by_id(uuid.uuid4()) is None


# --- List / filter ---


def test_get_all_filters_by_scan(repository, scan_job, db_session):
    other_target = Target(target="10.70.0.2", target_type=TargetType.IPV4)
    db_session.add(other_target)
    db_session.flush()
    other_scan = ScanJob(
        target_id=other_target.id, status=ScanStatus.COMPLETED, scan_type="full"
    )
    db_session.add(other_scan)
    db_session.flush()

    repository.create(_report(scan_job.id, generated_at=datetime.now(UTC)))
    repository.create(
        _report(
            other_scan.id,
            generated_at=datetime.now(UTC) + timedelta(seconds=1),
        )
    )

    items, total = repository.get_all(scan_id=scan_job.id)
    assert total == 1
    assert items[0].scan_id == scan_job.id


def test_get_all_lists_every_report_without_filter(repository, scan_job):
    repository.create(_report(scan_job.id, generated_at=datetime.now(UTC)))
    repository.create(
        _report(scan_job.id, generated_at=datetime.now(UTC) + timedelta(seconds=1))
    )
    items, total = repository.get_all()
    assert total == 2


def test_get_latest_by_scan_returns_most_recent(repository, scan_job):
    older = repository.create(_report(scan_job.id, generated_at=datetime.now(UTC)))
    newer = repository.create(
        _report(scan_job.id, generated_at=datetime.now(UTC) + timedelta(seconds=5))
    )
    latest = repository.get_latest_by_scan(scan_job.id)
    assert latest.id == newer.id
    assert latest.id != older.id


# --- Logical identity / uniqueness ---


def test_duplicate_scan_and_generated_at_rejected(db_session, scan_job):
    timestamp = datetime.now(UTC)
    first = _report(scan_job.id, generated_at=timestamp)
    db_session.add(first)
    db_session.flush()

    duplicate = _report(scan_job.id, generated_at=timestamp)
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_repeated_generation_creates_new_immutable_row(repository, scan_job):
    """Unlike Module 06/07's upsert pattern, reports are never updated in
    place: each successful generation is a new historical row."""
    first = repository.create(_report(scan_job.id, generated_at=datetime.now(UTC)))
    second = repository.create(
        _report(scan_job.id, generated_at=datetime.now(UTC) + timedelta(seconds=1))
    )
    assert first.id != second.id

    items, total = repository.get_all(scan_id=scan_job.id)
    assert total == 2


# --- Repository never commits ---


def test_create_does_not_commit(db_session, repository, scan_job):
    repository.create(_report(scan_job.id))
    db_session.rollback()
    remaining = db_session.query(Report).filter(Report.scan_id == scan_job.id).count()
    assert remaining == 0


def test_delete_does_not_commit(db_session, repository, scan_job):
    report = repository.create(_report(scan_job.id))
    db_session.commit()

    repository.delete(report)
    db_session.rollback()

    remaining = db_session.query(Report).filter(Report.id == report.id).count()
    assert remaining == 1
