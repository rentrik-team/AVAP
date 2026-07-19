import pytest

from app.core.enums import ScanStatus, TargetType
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.repositories.scan_repository import ScanRepository


@pytest.fixture
def scan_repository(db_session):
    return ScanRepository(db_session)


@pytest.fixture
def test_target(db_session):
    target = Target(target="192.168.1.100", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)
    return target


def test_create_scan_job(scan_repository, test_target):
    scan_job = ScanJob(
        target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING
    )
    created_scan = scan_repository.create(scan_job)

    assert created_scan.id is not None
    assert created_scan.target_id == test_target.id
    assert created_scan.status == ScanStatus.PENDING
    assert created_scan.scan_type == "full"


def test_get_scan_by_id(scan_repository, test_target):
    scan_job = ScanJob(
        target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING
    )
    created_scan = scan_repository.create(scan_job)

    retrieved_scan = scan_repository.get_by_id(created_scan.id)
    assert retrieved_scan is not None
    assert retrieved_scan.id == created_scan.id


def test_get_all_scans(scan_repository, test_target):
    scan_job1 = ScanJob(
        target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING
    )
    scan_job2 = ScanJob(
        target_id=test_target.id, scan_type="quick", status=ScanStatus.RUNNING
    )
    scan_repository.create(scan_job1)
    scan_repository.create(scan_job2)

    scans = scan_repository.get_all()
    assert len(scans) >= 2


def test_update_scan(scan_repository, test_target):
    scan_job = ScanJob(
        target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING
    )
    created_scan = scan_repository.create(scan_job)

    created_scan.status = ScanStatus.COMPLETED
    updated_scan = scan_repository.update(created_scan)

    assert updated_scan.status == ScanStatus.COMPLETED


def test_delete_scan(scan_repository, test_target):
    scan_job = ScanJob(
        target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING
    )
    created_scan = scan_repository.create(scan_job)

    scan_repository.delete(created_scan)
    assert scan_repository.get_by_id(created_scan.id) is None


def test_get_running_scans(scan_repository, test_target):
    """PENDING counts as active alongside RUNNING: a scan job is created as
    PENDING and only flips to RUNNING once its background execution thread
    picks it up, so the duplicate-scan guard must treat both as active to
    avoid a race where a second scan slips in during that window.
    """
    scan_job1 = ScanJob(
        target_id=test_target.id, scan_type="full", status=ScanStatus.RUNNING
    )
    scan_job2 = ScanJob(
        target_id=test_target.id, scan_type="quick", status=ScanStatus.PENDING
    )
    scan_job3 = ScanJob(
        target_id=test_target.id, scan_type="quick", status=ScanStatus.COMPLETED
    )
    scan_repository.create(scan_job1)
    scan_repository.create(scan_job2)
    scan_repository.create(scan_job3)

    running_scans = scan_repository.get_running_scans_for_target(test_target.id)
    assert {scan.status for scan in running_scans} == {
        ScanStatus.RUNNING,
        ScanStatus.PENDING,
    }
    assert len(running_scans) == 2


# --- Repository never commits ---


def test_create_does_not_commit(scan_repository, test_target, db_session):
    scan_job = ScanJob(
        target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING
    )
    created = scan_repository.create(scan_job)
    created_id = created.id

    # Rolling back must undo the write, proving the repository only flushed.
    db_session.rollback()

    assert scan_repository.get_by_id(created_id) is None


def test_update_does_not_commit(scan_repository, test_target, db_session):
    scan_job = ScanJob(
        target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING
    )
    created = scan_repository.create(scan_job)
    db_session.commit()

    created.status = ScanStatus.COMPLETED
    scan_repository.update(created)
    db_session.rollback()

    reloaded = scan_repository.get_by_id(created.id)
    assert reloaded.status == ScanStatus.PENDING


def test_delete_does_not_commit(scan_repository, test_target, db_session):
    scan_job = ScanJob(
        target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING
    )
    created = scan_repository.create(scan_job)
    db_session.commit()
    created_id = created.id

    scan_repository.delete(created)
    db_session.rollback()

    assert scan_repository.get_by_id(created_id) is not None
