import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.enums import (
    AuditActorType,
    AuditEventCategory,
    AuditEventType,
    AuditOutcome,
    AuditResourceType,
)
from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository


@pytest.fixture
def repository(db_session):
    return AuditRepository(db_session)


def _event(
    event_type=AuditEventType.TARGET_CREATED,
    category=AuditEventCategory.TARGET,
    outcome=AuditOutcome.SUCCESS,
    actor_type=AuditActorType.ANONYMOUS,
    resource_type=AuditResourceType.TARGET,
    resource_id=None,
    scan_id=None,
    occurred_at=None,
    **kw,
):
    return AuditEvent(
        event_type=event_type,
        category=category,
        outcome=outcome,
        actor_type=actor_type,
        resource_type=resource_type,
        resource_id=resource_id or uuid.uuid4(),
        scan_id=scan_id,
        event_metadata=kw.pop("event_metadata", {}),
        occurred_at=occurred_at or datetime.now(UTC),
        **kw,
    )


# --- Append / get ---


def test_append_persists_event(repository):
    event = repository.append(_event())
    assert event.id is not None


def test_get_by_id_returns_event(repository):
    created = repository.append(_event())
    fetched = repository.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id


def test_get_by_id_returns_none_when_absent(repository):
    assert repository.get_by_id(uuid.uuid4()) is None


# --- No mutation methods exist ---


def test_repository_exposes_no_update_method(repository):
    assert not hasattr(repository, "update")


def test_repository_exposes_no_delete_method(repository):
    assert not hasattr(repository, "delete")


def test_repository_exposes_no_upsert_method(repository):
    assert not hasattr(repository, "upsert")


# --- Repository does not commit ---


def test_append_does_not_commit(db_session, repository):
    repository.append(_event())
    db_session.rollback()
    remaining = db_session.query(AuditEvent).count()
    assert remaining == 0


# --- Filtering ---


def test_list_filters_by_event_type(repository):
    repository.append(_event(event_type=AuditEventType.TARGET_CREATED))
    repository.append(_event(event_type=AuditEventType.TARGET_DELETED))

    items, total = repository.list(event_type=AuditEventType.TARGET_DELETED)
    assert total == 1
    assert items[0].event_type == AuditEventType.TARGET_DELETED


def test_list_filters_by_category(repository):
    repository.append(_event(category=AuditEventCategory.TARGET))
    repository.append(
        _event(
            event_type=AuditEventType.SCAN_CREATED,
            category=AuditEventCategory.SCAN,
            resource_type=AuditResourceType.SCAN,
        )
    )

    items, total = repository.list(category=AuditEventCategory.SCAN)
    assert total == 1
    assert items[0].category == AuditEventCategory.SCAN


def test_list_filters_by_outcome(repository):
    repository.append(_event(outcome=AuditOutcome.SUCCESS))
    repository.append(
        _event(
            event_type=AuditEventType.RISK_CALCULATION_FAILED,
            category=AuditEventCategory.RISK,
            outcome=AuditOutcome.FAILURE,
            resource_type=AuditResourceType.SCAN,
        )
    )

    items, total = repository.list(outcome=AuditOutcome.FAILURE)
    assert total == 1
    assert items[0].outcome == AuditOutcome.FAILURE


def test_list_filters_by_resource(repository):
    target_id = uuid.uuid4()
    repository.append(_event(resource_id=target_id))
    repository.append(_event(resource_id=uuid.uuid4()))

    items, total = repository.list(
        resource_type=AuditResourceType.TARGET, resource_id=target_id
    )
    assert total == 1
    assert items[0].resource_id == target_id


def test_list_filters_by_scan_id(repository):
    scan_id = uuid.uuid4()
    repository.append(
        _event(
            event_type=AuditEventType.SCAN_CREATED,
            category=AuditEventCategory.SCAN,
            resource_type=AuditResourceType.SCAN,
            resource_id=scan_id,
            scan_id=scan_id,
        )
    )
    repository.append(_event())

    items, total = repository.list(scan_id=scan_id)
    assert total == 1
    assert items[0].scan_id == scan_id


def test_list_filters_by_actor_type(repository):
    repository.append(_event(actor_type=AuditActorType.SYSTEM))
    repository.append(_event(actor_type=AuditActorType.ANONYMOUS))

    items, total = repository.list(actor_type=AuditActorType.SYSTEM)
    assert total == 1
    assert items[0].actor_type == AuditActorType.SYSTEM


def test_list_filters_by_date_range(repository):
    now = datetime.now(UTC)
    repository.append(_event(occurred_at=now - timedelta(days=2)))
    recent = repository.append(_event(occurred_at=now))

    items, total = repository.list(occurred_after=now - timedelta(hours=1))
    assert total == 1
    assert items[0].id == recent.id


# --- Deterministic ordering / pagination ---


def test_list_orders_by_occurred_at_desc(repository):
    now = datetime.now(UTC)
    older = repository.append(_event(occurred_at=now - timedelta(minutes=5)))
    newer = repository.append(_event(occurred_at=now))

    items, total = repository.list()
    assert total == 2
    assert items[0].id == newer.id
    assert items[1].id == older.id


def test_list_respects_limit_and_skip(repository):
    for _ in range(5):
        repository.append(_event())

    items, total = repository.list(skip=0, limit=2)
    assert total == 5
    assert len(items) == 2

    items_page_2, _ = repository.list(skip=2, limit=2)
    assert len(items_page_2) == 2
    assert items[0].id != items_page_2[0].id


def test_list_empty_database_returns_empty(repository):
    items, total = repository.list()
    assert items == []
    assert total == 0
