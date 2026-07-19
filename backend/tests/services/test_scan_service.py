import tempfile
import threading
import uuid
from pathlib import Path

import pytest

from app.ai.provider import AIProviderResponse
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


class _NoOpAIManager:
    """Stands in for AIManager so the background pipeline's AI vulnerability
    discovery step never makes a real network call during tests — it always
    returns zero findings instantly. A real AIManager() would otherwise be
    constructed by default and call whatever provider/key is configured in
    the environment's .env, making the suite network-dependent and slow."""

    def generate(self, prompt):
        return AIProviderResponse(content='{"findings": []}', provider="test", model="test")


# A minimal, valid Nmap XML report so a "successful" mock dispatch can be
# parsed for real by ParserManager -> InventoryService, exercising the full
# background pipeline rather than stopping at a fabricated artifact.
_MOCK_NMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap -sV -oX test.xml 10.0.0.1" version="7.92">
  <host>
    <status state="up" reason="arp-response"/>
    <address addr="10.0.0.1" addrtype="ipv4"/>
    <ports>
      <port protocol="tcp" portid="80">
        <state state="open" reason="syn-ack" reason_ttl="64"/>
        <service name="http" product="Apache httpd" version="2.4.41" method="probed" conf="10"/>
      </port>
    </ports>
  </host>
</nmaprun>
"""


def _write_mock_nmap_output() -> Path:
    with tempfile.NamedTemporaryFile(
        suffix=".xml", mode="w", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(_MOCK_NMAP_XML)
        return Path(tmp.name)


class MockScannerEngine(IScannerEngine):
    """Dispatches instantly unless `block` is set, in which case it waits on
    `release_event` — lets tests observe the RUNNING state deterministically
    before the background thread races ahead to a terminal status."""

    def __init__(self, block: bool = False):
        self.dispatched = False
        self.block = block
        self.dispatch_started_event = threading.Event()
        self.release_event = threading.Event()

    def dispatch_scan(
        self, scan_id: uuid.UUID, target: str, scan_profile: str, scanner_type=None
    ):
        self.dispatched = True
        self.dispatch_started_event.set()
        if self.block:
            self.release_event.wait(timeout=5)

        from app.core.enums import ExecutionStatus
        from app.scanners.scan_artifact import ScanArtifact

        return ScanArtifact(
            scan_id=scan_id,
            execution_status=ExecutionStatus.SUCCESS,
            output_path=_write_mock_nmap_output(),
        )


@pytest.fixture
def scan_service(db_session):
    scan_repo = ScanRepository(db_session)
    target_repo = TargetRepository(db_session)
    scanner_engine = MockScannerEngine()
    audit_service = AuditService(AuditRepository(db_session))
    service = ScanService(
        scan_repo,
        target_repo,
        audit_service,
        scanner_engine,
        # Background scan execution normally opens (and closes) its own
        # session; tests instead reuse the shared transactional db_session
        # so assertions can see what the background thread persisted, and
        # must not let it be closed out from under the test.
        session_factory=lambda: db_session,
        session_finalizer=lambda s: None,
        ai_manager=_NoOpAIManager(),
    )
    yield service
    # The background pipeline now does real work (parse/inventory/AI/risk),
    # so it can outlive a test that doesn't explicitly join it. Join here
    # unconditionally so no thread is left running against db_session after
    # this fixture's teardown, which would race the db_session fixture's own
    # teardown (connection close) that runs right after this one.
    if service.last_scan_thread is not None:
        service.last_scan_thread.join(timeout=5)


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
    # Dispatch happens on a background thread — immediately after
    # create_scan() returns, it must not have run yet.
    assert scan_job.status == ScanStatus.PENDING

    # Deterministically wait for the background thread rather than racing
    # it, then confirm it ran the engine and drove the job to completion.
    scan_service.last_scan_thread.join(timeout=5)
    scan_service.scan_repository.session.refresh(scan_job)

    assert scan_service.scanner_engine.dispatched is True
    assert scan_job.status == ScanStatus.COMPLETED
    assert scan_job.started_at is not None
    assert scan_job.completed_at is not None


def test_create_scan_target_not_found(scan_service):
    request = CreateScanRequest(target_id=uuid.uuid4(), scan_profile="full")
    with pytest.raises(NotFoundException):
        scan_service.create_scan(request)


def test_create_scan_already_running(db_session, test_target):
    # A blocking engine keeps the first scan's background thread parked
    # (past its RUNNING commit, inside dispatch_scan) for the duration of
    # this test — the duplicate check only needs PENDING/RUNNING status,
    # but the second create_scan() call still touches the same db_session
    # the first scan's thread is using, which isn't safe to race.
    blocking_engine = MockScannerEngine(block=True)
    scan_service = ScanService(
        ScanRepository(db_session),
        TargetRepository(db_session),
        AuditService(AuditRepository(db_session)),
        blocking_engine,
        session_factory=lambda: db_session,
        session_finalizer=lambda s: None,
        ai_manager=_NoOpAIManager(),
    )
    request = CreateScanRequest(target_id=test_target.id, scan_profile="full")
    scan_service.create_scan(request)
    assert blocking_engine.dispatch_started_event.wait(timeout=5)

    with pytest.raises(ConflictException):
        scan_service.create_scan(request)

    blocking_engine.release_event.set()
    scan_service.last_scan_thread.join(timeout=5)


def test_get_scan(scan_service, test_target):
    request = CreateScanRequest(target_id=test_target.id, scan_profile="full")
    created_scan = scan_service.create_scan(request)

    # Join before touching the shared session again from this thread: the
    # background thread uses the same db_session, which isn't safe for
    # concurrent multi-thread access.
    scan_service.last_scan_thread.join(timeout=5)

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


def test_delete_running_scan_fails(db_session, test_target):
    # A blocking engine holds the scan in RUNNING deterministically instead
    # of racing the background thread to a terminal status.
    blocking_engine = MockScannerEngine(block=True)
    scan_service = ScanService(
        ScanRepository(db_session),
        TargetRepository(db_session),
        AuditService(AuditRepository(db_session)),
        blocking_engine,
        session_factory=lambda: db_session,
        session_finalizer=lambda s: None,
        ai_manager=_NoOpAIManager(),
    )
    request = CreateScanRequest(target_id=test_target.id, scan_profile="full")
    created_scan = scan_service.create_scan(request)

    assert blocking_engine.dispatch_started_event.wait(timeout=5)

    with pytest.raises(ConflictException):
        scan_service.delete_scan(created_scan.id)

    blocking_engine.release_event.set()
    scan_service.last_scan_thread.join(timeout=5)


class _NoOutputScannerEngine(IScannerEngine):
    """Dispatches successfully but with no output_path — simulates a scanner
    that reported success without producing a parseable artifact, so the
    parser stage itself fails."""

    def dispatch_scan(self, scan_id, target, scan_profile, scanner_type=None):
        from app.core.enums import ExecutionStatus
        from app.scanners.scan_artifact import ScanArtifact

        return ScanArtifact(scan_id=scan_id, execution_status=ExecutionStatus.SUCCESS)


def test_create_scan_marks_failed_on_parser_error(db_session, test_target):
    """A successful dispatch with no parseable output must still resolve to
    a terminal FAILED status, not leave the scan stuck at RUNNING — this is
    the ParserException branch of _process_successful_scan."""
    scan_service = ScanService(
        ScanRepository(db_session),
        TargetRepository(db_session),
        AuditService(AuditRepository(db_session)),
        _NoOutputScannerEngine(),
        session_factory=lambda: db_session,
        session_finalizer=lambda s: None,
        ai_manager=_NoOpAIManager(),
    )
    request = CreateScanRequest(target_id=test_target.id, scan_profile="full")
    created_scan = scan_service.create_scan(request)

    scan_service.last_scan_thread.join(timeout=5)
    db_session.refresh(created_scan)

    assert created_scan.status == ScanStatus.FAILED
    assert created_scan.failure_reason is not None
    assert created_scan.completed_at is not None


def test_create_scan_success_auto_calculates_risk(scan_service, test_target, db_session):
    """A completed scan's discovered inventory should automatically get a
    risk assessment, without any separate manual trigger."""
    from app.core.enums import RiskScope
    from app.models.risk_assessment import RiskAssessment

    request = CreateScanRequest(target_id=test_target.id, scan_profile="full")
    scan_job = scan_service.create_scan(request)
    scan_service.last_scan_thread.join(timeout=5)
    db_session.refresh(scan_job)

    assert scan_job.status == ScanStatus.COMPLETED

    scan_risk = (
        db_session.query(RiskAssessment)
        .filter_by(scan_id=scan_job.id, scope=RiskScope.SCAN)
        .one_or_none()
    )
    assert scan_risk is not None


def test_get_all_scans_filters_by_target_id(db_session, target_repo):
    """A target's own scans must be retrievable in isolation from other
    targets' scans — this is what lets the Target detail page list only
    that target's scan history."""
    target_a = Target(target="10.5.0.1", target_type=TargetType.IPV4)
    target_b = Target(target="10.5.0.2", target_type=TargetType.IPV4)
    target_repo.create(target_a)
    target_repo.create(target_b)

    scan_repo = ScanRepository(db_session)
    from app.models.scan_job import ScanJob

    scan_repo.create(ScanJob(target_id=target_a.id, scan_type="full", status=ScanStatus.COMPLETED))
    scan_repo.create(ScanJob(target_id=target_b.id, scan_type="full", status=ScanStatus.COMPLETED))
    scan_repo.create(ScanJob(target_id=target_a.id, scan_type="full", status=ScanStatus.FAILED))

    service = ScanService(
        scan_repo,
        target_repo,
        AuditService(AuditRepository(db_session)),
    )

    scans = service.get_all_scans(target_id=target_a.id)
    total = service.count_scans(target_id=target_a.id)

    assert total == 2
    assert {s.target_id for s in scans} == {target_a.id}
