import uuid
import pytest
from fastapi.testclient import TestClient
from app.core.enums import TargetType
from app.api.routes.v1.scans import get_scan_service
from app.services.scan_service import ScanService
from app.repositories.scan_repository import ScanRepository
from app.repositories.target_repository import TargetRepository
from app.scanners.interfaces import IScannerEngine
from app.scanners.scan_artifact import ScanArtifact
from app.core.enums import ExecutionStatus
from app.main import app


class MockScannerEngine(IScannerEngine):
    def dispatch_scan(self, scan_id: uuid.UUID, target: str, scan_profile: str, scanner_type=None):
        return ScanArtifact(
            scan_id=scan_id,
            execution_status=ExecutionStatus.SUCCESS,
            stdout="Mock output"
        )


@pytest.fixture(autouse=True)
def override_scan_service(db_session):
    def mock_get_scan_service():
        return ScanService(
            scan_repository=ScanRepository(db_session),
            target_repository=TargetRepository(db_session),
            scanner_engine=MockScannerEngine()
        )
    app.dependency_overrides[get_scan_service] = mock_get_scan_service
    yield
    app.dependency_overrides.pop(get_scan_service, None)


@pytest.fixture
def setup_target(client: TestClient):
    response = client.post("/api/v1/targets/", json={"target": "10.0.0.100"})
    assert response.status_code == 201
    return response.json()


def test_create_scan(client: TestClient, setup_target):
    target_id = setup_target["id"]
    response = client.post(
        "/api/v1/scans/", 
        json={"target_id": target_id, "scan_profile": "full", "priority": "normal"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "scan_id" in data
    assert data["target_id"] == target_id
    assert data["status"] == "RUNNING"  # Now RUNNING since engine successfully dispatches


def test_list_scans(client: TestClient, setup_target):
    target_id = setup_target["id"]
    client.post("/api/v1/scans/", json={"target_id": target_id, "scan_profile": "full"})
    
    response = client.get("/api/v1/scans/")
    assert response.status_code == 200
    data = response.json()
    assert "scans" in data
    assert "total" in data
    assert len(data["scans"]) >= 1


def test_get_scan(client: TestClient, setup_target):
    target_id = setup_target["id"]
    create_response = client.post(
        "/api/v1/scans/", 
        json={"target_id": target_id, "scan_profile": "full"}
    )
    scan_id = create_response.json()["scan_id"]
    
    response = client.get(f"/api/v1/scans/{scan_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["scan_id"] == scan_id


def test_get_scan_status(client: TestClient, setup_target):
    target_id = setup_target["id"]
    create_response = client.post(
        "/api/v1/scans/", 
        json={"target_id": target_id, "scan_profile": "full"}
    )
    scan_id = create_response.json()["scan_id"]
    
    response = client.get(f"/api/v1/scans/{scan_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["scan_id"] == scan_id
    assert "status" in data


def test_delete_scan(client: TestClient, setup_target):
    target_id = setup_target["id"]
    create_response = client.post(
        "/api/v1/scans/", 
        json={"target_id": target_id, "scan_profile": "full"}
    )
    scan_id = create_response.json()["scan_id"]
    
    response = client.delete(f"/api/v1/scans/{scan_id}")
    assert response.status_code == 204
    
    get_response = client.get(f"/api/v1/scans/{scan_id}")
    assert get_response.status_code == 404
