import uuid

import pytest

from app.core.enums import ScanStatus, TargetType
from app.core.exceptions import ConflictException, NotFoundException
from app.models.target import Target
from app.repositories.audit_repository import AuditRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.target_repository import TargetRepository
from app.scanners.interfaces import IScannerEngine
from app.schemas.scan import CreateScanRequest
from app.services.audit_service import AuditService
from app.services.scan_service import ScanService


class MockScannerEngine(IScannerEngine):
    def __init__(self):
        self.dispatched = False

    def dispatch_scan(
        self, scan_id: uuid.UUID, target: str, scan_profile: str, scanner_type=None
    ):
        self.dispatched = True
        from app.core.enums import ExecutionStatus
        from app.scanners.scan_artifact import ScanArtifact

        return ScanArtifact(scan_id=scan_id, execution_status=ExecutionStatus.SUCCESS)


@pytest.fixture
def scan_service(db_session):
    scan_repo = ScanRepository(db_session)
    target_repo = TargetRepository(db_session)
    scanner_engine = MockScannerEngine()
    audit_service = AuditService(AuditRepository(db_session))
    return ScanService(scan_repo, target_repo, audit_service, scanner_engine)


@pytest.fixture
def target_repo(db_session):
    return TargetRepository(db_session)


@pytest.fixture
def test_target(target_repo):
    target = Target(target="10.0.0.1", target_type=TargetType.IPV4)
    return target_repo.create(target)


def test_create_scan_success(scan_service, test_target):
    request = CreateScanRequest(target_id=test_target.id, scan_profile="full")
    scan_job = scan_service.create_scan(request)

    assert scan_job.id is not None
    assert scan_job.target_id == test_target.id
    # Should be RUNNING because we have a scanner engine attached
    assert scan_job.status == ScanStatus.RUNNING
    assert scan_service.scanner_engine.dispatched is True


def test_create_scan_target_not_found(scan_service):
    request = CreateScanRequest(target_id=uuid.uuid4(), scan_profile="full")
    with pytest.raises(NotFoundException):
        scan_service.create_scan(request)


def test_create_scan_already_running(scan_service, test_target):
    request = CreateScanRequest(target_id=test_target.id, scan_profile="full")
    scan_service.create_scan(request)

    # Try to create another scan for the same target
    with pytest.raises(ConflictException):
        scan_service.create_scan(request)


def test_get_scan(scan_service, test_target):
    request = CreateScanRequest(target_id=test_target.id, scan_profile="full")
    created_scan = scan_service.create_scan(request)

    retrieved_scan = scan_service.get_scan(created_scan.id)
    assert retrieved_scan.id == created_scan.id


def test_get_scan_not_found(scan_service):
    with pytest.raises(NotFoundException):
        scan_service.get_scan(uuid.uuid4())


def test_delete_scan(scan_service, test_target):
    # Create with no engine to keep it PENDING
    scan_service_no_engine = ScanService(
        scan_repository=scan_service.scan_repository,
        target_repository=scan_service.target_repository,
        audit_service=scan_service.audit_service,
        scanner_engine=None,
    )
    request = CreateScanRequest(target_id=test_target.id, scan_profile="full")
    created_scan = scan_service_no_engine.create_scan(request)

    scan_service_no_engine.delete_scan(created_scan.id)

    with pytest.raises(NotFoundException):
        scan_service_no_engine.get_scan(created_scan.id)


def test_delete_running_scan_fails(scan_service, test_target):
    request = CreateScanRequest(target_id=test_target.id, scan_profile="full")
    created_scan = scan_service.create_scan(request)

    with pytest.raises(ConflictException):
        scan_service.delete_scan(created_scan.id)
