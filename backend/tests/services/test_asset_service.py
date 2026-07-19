import uuid

import pytest

from app.core.enums import ScanStatus, TargetType
from app.core.exceptions import NotFoundException
from app.models.asset import Asset
from app.models.scan_finding import ScanFinding
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.repositories.asset_repository import AssetRepository
from app.services.asset_service import AssetService


@pytest.fixture
def service(db_session):
    return AssetService(AssetRepository(db_session))


@pytest.fixture
def asset(db_session):
    a = Asset(ipv4="192.168.50.1", hostname="svc-test.local")
    db_session.add(a)
    db_session.commit()
    return a


def test_get_all_assets(service, asset):
    items, total = service.get_all_assets()
    assert total == 1
    assert items[0].id == asset.id


def test_get_all_assets_filters_by_target_id(service, db_session):
    """Asset has no direct target_id — reached only via Target <- ScanJob <-
    ScanFinding. An asset discovered by a different target's scan must be
    excluded."""
    target_a = Target(target="10.0.0.1", target_type=TargetType.IPV4)
    target_b = Target(target="10.0.0.2", target_type=TargetType.IPV4)
    db_session.add_all([target_a, target_b])
    db_session.flush()

    scan_a = ScanJob(target_id=target_a.id, scan_type="full", status=ScanStatus.COMPLETED)
    scan_b = ScanJob(target_id=target_b.id, scan_type="full", status=ScanStatus.COMPLETED)
    db_session.add_all([scan_a, scan_b])
    db_session.flush()

    asset_a = Asset(ipv4="10.0.0.1")
    asset_b = Asset(ipv4="10.0.0.2")
    db_session.add_all([asset_a, asset_b])
    db_session.flush()

    db_session.add_all(
        [
            ScanFinding(scan_id=scan_a.id, asset_id=asset_a.id),
            ScanFinding(scan_id=scan_b.id, asset_id=asset_b.id),
        ]
    )
    db_session.commit()

    items, total = service.get_all_assets(target_id=target_a.id)
    assert total == 1
    assert items[0].id == asset_a.id


def test_get_asset_not_found(service):
    with pytest.raises(NotFoundException):
        service.get_asset(uuid.uuid4())


def test_delete_asset_commits(service, asset, db_session):
    asset_id = asset.id
    service.delete_asset(asset_id)

    # A rollback here must NOT undo the deletion, proving the service (not
    # the caller) already committed the transaction.
    db_session.rollback()

    assert db_session.get(Asset, asset_id) is None


def test_delete_asset_not_found(service):
    with pytest.raises(NotFoundException):
        service.delete_asset(uuid.uuid4())
