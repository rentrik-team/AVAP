import tempfile
import threading
import time
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes.v1.scans import get_scan_service
from app.core.enums import ExecutionStatus, ScanStatus
from app.main import app
from app.models.scan_job import ScanJob
from app.repositories.audit_repository import AuditRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.target_repository import TargetRepository
from app.scanners.interfaces import IScannerEngine
from app.scanners.scan_artifact import ScanArtifact
from app.ai.provider import AIProviderResponse
from app.services.audit_service import AuditService
from app.services.scan_service import ScanService


class _NoOpAIManager:
    """Stands in for AIManager so the background pipeline's AI vulnerability
    discovery step never makes a real network call during tests — see the
    identical test double in tests/services/test_scan_service.py for why."""

    def generate(self, prompt):
        return AIProviderResponse(content='{"findings": []}', provider="test", model="test")


# A minimal, valid Nmap XML report so a "successful" mock dispatch can be
# parsed for real by ParserManager -> InventoryService, exercising the full
# background pipeline (not just the scan-lifecycle status transitions).
_MOCK_NMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap -sV -oX test.xml 10.0.0.100" version="7.92">
  <host>
    <status state="up" reason="arp-response"/>
    <address addr="10.0.0.100" addrtype="ipv4"/>
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
        self.block = block
        self.dispatch_started_event = threading.Event()
        self.release_event = threading.Event()

    def dispatch_scan(
        self, scan_id: uuid.UUID, target: str, scan_profile: str, scanner_type=None
    ):
        self.dispatch_started_event.set()
        if self.block:
            self.release_event.wait(timeout=5)
        return ScanArtifact(
            scan_id=scan_id,
            execution_status=ExecutionStatus.SUCCESS,
            stdout="Mock output",
            output_path=_write_mock_nmap_output(),
        )


def wait_for_status(client: TestClient, scan_id: str, expected: str, timeout: float = 5.0):
    """Poll GET /scans/{id}/status until it reports `expected`.

    Scan dispatch runs on a background thread now, so its status transitions
    asynchronously relative to the HTTP request that created it — tests must
    wait for a status rather than assuming it's already reflected.
    """
    deadline = time.monotonic() + timeout
    last_seen = None
    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/scans/{scan_id}/status")
        last_seen = response.json()["data"]["status"]
        if last_seen == expected:
            return
        time.sleep(0.02)
    raise AssertionError(f"scan {scan_id} never reached {expected!r} (last saw {last_seen!r})")


@pytest.fixture(autouse=True)
def override_scan_service(db_session):
    engine = MockScannerEngine()
    created_services: list[ScanService] = []

    def mock_get_scan_service():
        service = ScanService(
            scan_repository=ScanRepository(db_session),
            target_repository=TargetRepository(db_session),
            audit_service=AuditService(AuditRepository(db_session)),
            scanner_engine=engine,
            # Background scan execution normally opens (and closes) its own
            # session; reuse the shared transactional db_session instead so
            # the test can observe what the background thread persisted.
            session_factory=lambda: db_session,
            session_finalizer=lambda s: None,
            ai_manager=_NoOpAIManager(),
        )
        created_services.append(service)
        return service

    app.dependency_overrides[get_scan_service] = mock_get_scan_service
    yield engine
    app.dependency_overrides.pop(get_scan_service, None)
    # The background pipeline now does real work (parse/inventory/AI/risk),
    # so it can outlive a test that doesn't explicitly wait for a terminal
    # status. Join here unconditionally so no thread is left running against
    # db_session after this fixture's teardown, which would race the
    # db_session fixture's own teardown (connection close) right after.
    for service in created_services:
        if service.last_scan_thread is not None:
            service.last_scan_thread.join(timeout=5)


@pytest.fixture
def setup_target(client: TestClient):
    response = client.post("/api/v1/targets/", json={"target": "10.0.0.100"})
    assert response.status_code == 201
    # Targets API responses use the standard SuccessResponse envelope
    # ({"success": ..., "data": {...}}); the target payload is under "data".
    return response.json()["data"]


def test_create_scan(client: TestClient, setup_target):
    target_id = setup_target["id"]
    response = client.post(
        "/api/v1/scans",
        json={"target_id": target_id, "scan_profile": "full", "priority": "normal"},
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert "scan_id" in data
    assert data["target_id"] == target_id
    # Dispatch runs on a background thread — the response returns before it
    # has necessarily started, so only PENDING is guaranteed immediately.
    assert data["status"] == "PENDING"

    wait_for_status(client, data["scan_id"], "COMPLETED")


def test_list_scans(client: TestClient, setup_target):
    target_id = setup_target["id"]
    create_response = client.post(
        "/api/v1/scans", json={"target_id": target_id, "scan_profile": "full"}
    )
    # Wait for the background thread to finish before this thread touches
    # db_session again — it isn't safe to use concurrently from two threads.
    wait_for_status(client, create_response.json()["data"]["scan_id"], "COMPLETED")

    response = client.get("/api/v1/scans")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "scans" in data
    assert "total" in data
    assert len(data["scans"]) >= 1


def test_get_scan(client: TestClient, setup_target):
    target_id = setup_target["id"]
    create_response = client.post(
        "/api/v1/scans", json={"target_id": target_id, "scan_profile": "full"}
    )
    scan_id = create_response.json()["data"]["scan_id"]
    # Wait for the background thread to finish before this thread touches
    # db_session again — it isn't safe to use concurrently from two threads.
    wait_for_status(client, scan_id, "COMPLETED")

    response = client.get(f"/api/v1/scans/{scan_id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["scan_id"] == scan_id


def test_get_scan_status(client: TestClient, setup_target):
    target_id = setup_target["id"]
    create_response = client.post(
        "/api/v1/scans", json={"target_id": target_id, "scan_profile": "full"}
    )
    scan_id = create_response.json()["data"]["scan_id"]

    response = client.get(f"/api/v1/scans/{scan_id}/status")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["scan_id"] == scan_id
    assert "status" in data


def test_delete_scan_conflict_while_running(
    client: TestClient, setup_target, override_scan_service
):
    """A scan dispatched to the Scanner Engine transitions to RUNNING and
    must not be deletable until it reaches a terminal state. This matches
    ScanService.delete_scan's business rule, not scan deletion generally.

    Uses a blocking engine so the scan reliably stays RUNNING long enough to
    attempt the delete, instead of racing the background thread to COMPLETED.
    """
    engine = override_scan_service
    engine.block = True
    target_id = setup_target["id"]
    create_response = client.post(
        "/api/v1/scans", json={"target_id": target_id, "scan_profile": "full"}
    )
    scan_id = create_response.json()["data"]["scan_id"]
    wait_for_status(client, scan_id, "RUNNING")

    response = client.delete(f"/api/v1/scans/{scan_id}")
    assert response.status_code == 409

    engine.release_event.set()
    wait_for_status(client, scan_id, "COMPLETED")


def test_delete_scan_succeeds_when_not_running(
    client: TestClient, db_session, setup_target
):
    """A scan in a terminal state (as set by Module 05 processing) can be deleted."""
    target_id = setup_target["id"]
    create_response = client.post(
        "/api/v1/scans", json={"target_id": target_id, "scan_profile": "full"}
    )
    scan_id = create_response.json()["data"]["scan_id"]
    # Let the background thread finish before touching db_session directly
    # from this thread — otherwise the two race on the same connection.
    wait_for_status(client, scan_id, "COMPLETED")

    scan_job = db_session.get(ScanJob, uuid.UUID(scan_id))
    scan_job.status = ScanStatus.COMPLETED
    db_session.commit()

    response = client.delete(f"/api/v1/scans/{scan_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/scans/{scan_id}")
    assert get_response.status_code == 404
