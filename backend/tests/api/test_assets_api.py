import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models.asset import Asset
from app.models.service import NetworkService


@pytest.fixture
def sample_data(db_session):
    """Create two assets with services for testing."""
    asset1 = Asset(ipv4="192.168.1.10", hostname="web-server.local", operating_system="Linux Ubuntu")
    asset2 = Asset(ipv4="192.168.1.20", hostname="db-server.local", operating_system="Linux Debian")
    db_session.add_all([asset1, asset2])
    db_session.flush()

    service1 = NetworkService(asset_id=asset1.id, port=80, protocol="tcp", service_name="http", product="Apache", version="2.4")
    service2 = NetworkService(asset_id=asset1.id, port=443, protocol="tcp", service_name="https", product="Apache", version="2.4")
    service3 = NetworkService(asset_id=asset2.id, port=5432, protocol="tcp", service_name="postgresql", product="PostgreSQL", version="13.0")
    db_session.add_all([service1, service2, service3])
    db_session.flush()

    return {"asset1": asset1, "asset2": asset2}


# --- List Assets ---

def test_list_assets(client: TestClient, sample_data):
    response = client.get("/api/v1/assets/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 2
    assert len(data["data"]["assets"]) == 2


def test_list_assets_pagination(client: TestClient, sample_data):
    response = client.get("/api/v1/assets/?skip=0&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 2
    assert len(data["data"]["assets"]) == 1


# --- Filters ---

def test_list_assets_ip_filtering(client: TestClient, sample_data):
    response = client.get("/api/v1/assets/?ip=192.168.1.20")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["assets"][0]["ipv4"] == "192.168.1.20"


def test_list_assets_hostname_filtering(client: TestClient, sample_data):
    response = client.get("/api/v1/assets/?hostname=web-server")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["assets"][0]["hostname"] == "web-server.local"


def test_list_assets_port_filtering(client: TestClient, sample_data):
    response = client.get("/api/v1/assets/?port=5432")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["assets"][0]["ipv4"] == "192.168.1.20"


# --- Detail ---

def test_get_asset_detail(client: TestClient, sample_data):
    asset_id = sample_data["asset1"].id
    response = client.get(f"/api/v1/assets/{asset_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == str(asset_id)
    assert len(data["data"]["services"]) == 2
    ports = {s["port"] for s in data["data"]["services"]}
    assert ports == {80, 443}


def test_get_asset_not_found(client: TestClient):
    response = client.get(f"/api/v1/assets/{uuid.uuid4()}")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"


# --- Delete ---

def test_delete_asset(client: TestClient, db_session, sample_data):
    asset_id = sample_data["asset1"].id

    response = client.delete(f"/api/v1/assets/{asset_id}")
    assert response.status_code == 204

    # Verify asset is gone
    asset = db_session.execute(select(Asset).where(Asset.id == asset_id)).scalar_one_or_none()
    assert asset is None

    # Verify CASCADE: services gone
    services = db_session.execute(select(NetworkService).where(NetworkService.asset_id == asset_id)).scalars().all()
    assert len(services) == 0


def test_delete_asset_not_found(client: TestClient):
    response = client.delete(f"/api/v1/assets/{uuid.uuid4()}")
    assert response.status_code == 404
