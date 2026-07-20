import pytest

from app.core.enums import TargetType
from app.core.exceptions import DuplicateException
from app.models.target import Target
from app.repositories.target_repository import TargetRepository


def test_create_and_get_target(db_session):
    repo = TargetRepository(db_session)

    target = Target(target="192.168.1.100", target_type=TargetType.IPV4)
    created = repo.create(target)

    assert created.id is not None
    assert created.target == "192.168.1.100"

    # Retrieve by ID
    retrieved = repo.get_by_id(created.id)
    assert retrieved is not None
    assert retrieved.id == created.id

    # Retrieve by value
    retrieved_by_value = repo.get_by_value("192.168.1.100")
    assert retrieved_by_value is not None
    assert retrieved_by_value.id == created.id


def test_create_duplicate_target_raises_exception(db_session):
    repo = TargetRepository(db_session)

    target1 = Target(target="duplicate.com", target_type=TargetType.HOSTNAME)
    repo.create(target1)

    target2 = Target(target="duplicate.com", target_type=TargetType.HOSTNAME)
    with pytest.raises(DuplicateException):
        repo.create(target2)


def test_get_all_pagination(db_session):
    repo = TargetRepository(db_session)

    # Create 5 targets
    for i in range(5):
        repo.create(Target(target=f"10.0.0.{i}", target_type=TargetType.IPV4))

    items, total = repo.get_all(skip=0, limit=3)
    assert total == 5
    assert len(items) == 3

    items, total = repo.get_all(skip=3, limit=3)
    assert total == 5
    assert len(items) == 2


def test_update_target(db_session):
    repo = TargetRepository(db_session)

    target = Target(target="192.168.1.50", target_type=TargetType.IPV4)
    created = repo.create(target)

    created.target = "192.168.1.51"
    updated = repo.update(created)

    assert updated.target == "192.168.1.51"

    # Verify in DB
    retrieved = repo.get_by_id(created.id)
    assert retrieved is not None
    assert retrieved.target == "192.168.1.51"


def test_delete_target(db_session):
    repo = TargetRepository(db_session)

    target = Target(target="10.1.1.1", target_type=TargetType.IPV4)
    created = repo.create(target)

    repo.delete(created)

    assert repo.get_by_id(created.id) is None


# --- Repository never commits ---


def test_create_does_not_commit(db_session):
    repo = TargetRepository(db_session)
    created = repo.create(Target(target="10.5.5.1", target_type=TargetType.IPV4))
    created_id = created.id

    # Rolling back must undo the write, proving the repository only flushed.
    db_session.rollback()

    assert repo.get_by_id(created_id) is None


def test_update_does_not_commit(db_session):
    repo = TargetRepository(db_session)
    created = repo.create(Target(target="10.5.5.2", target_type=TargetType.IPV4))
    db_session.commit()
    db_session.refresh(created)

    created.target = "10.5.5.3"
    repo.update(created)
    db_session.rollback()

    reloaded = repo.get_by_id(created.id)
    assert reloaded is not None
    assert reloaded.target == "10.5.5.2"


def test_delete_does_not_commit(db_session):
    repo = TargetRepository(db_session)
    created = repo.create(Target(target="10.5.5.4", target_type=TargetType.IPV4))
    db_session.commit()
    created_id = created.id

    repo.delete(created)
    db_session.rollback()

    assert repo.get_by_id(created_id) is not None
