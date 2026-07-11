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
    scan_job = ScanJob(target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING)
    created_scan = scan_repository.create(scan_job)
    
    assert created_scan.id is not None
    assert created_scan.target_id == test_target.id
    assert created_scan.status == ScanStatus.PENDING
    assert created_scan.scan_type == "full"


def test_get_scan_by_id(scan_repository, test_target):
    scan_job = ScanJob(target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING)
    created_scan = scan_repository.create(scan_job)
    
    retrieved_scan = scan_repository.get_by_id(created_scan.id)
    assert retrieved_scan is not None
    assert retrieved_scan.id == created_scan.id


def test_get_all_scans(scan_repository, test_target):
    scan_job1 = ScanJob(target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING)
    scan_job2 = ScanJob(target_id=test_target.id, scan_type="quick", status=ScanStatus.RUNNING)
    scan_repository.create(scan_job1)
    scan_repository.create(scan_job2)
    
    scans = scan_repository.get_all()
    assert len(scans) >= 2


def test_update_scan(scan_repository, test_target):
    scan_job = ScanJob(target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING)
    created_scan = scan_repository.create(scan_job)
    
    created_scan.status = ScanStatus.COMPLETED
    updated_scan = scan_repository.update(created_scan)
    
    assert updated_scan.status == ScanStatus.COMPLETED


def test_delete_scan(scan_repository, test_target):
    scan_job = ScanJob(target_id=test_target.id, scan_type="full", status=ScanStatus.PENDING)
    created_scan = scan_repository.create(scan_job)
    
    scan_repository.delete(created_scan)
    assert scan_repository.get_by_id(created_scan.id) is None


def test_get_running_scans(scan_repository, test_target):
    scan_job1 = ScanJob(target_id=test_target.id, scan_type="full", status=ScanStatus.RUNNING)
    scan_job2 = ScanJob(target_id=test_target.id, scan_type="quick", status=ScanStatus.PENDING)
    scan_repository.create(scan_job1)
    scan_repository.create(scan_job2)
    
    running_scans = scan_repository.get_running_scans_for_target(test_target.id)
    assert len(running_scans) == 1
    assert running_scans[0].status == ScanStatus.RUNNING
