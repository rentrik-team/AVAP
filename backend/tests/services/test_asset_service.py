import uuid

import pytest

from app.core.exceptions import NotFoundException
from app.models.asset import Asset
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
