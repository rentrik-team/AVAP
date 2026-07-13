import uuid

from fastapi.testclient import TestClient

from app.audit.context import ActorContext, AuditContext, RequestContext
from app.core.enums import (
    AuditEventCategory,
    AuditEventType,
    AuditOutcome,
    AuditResourceType,
)
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService


def _seed_event(
    db_session, event_type=AuditEventType.TARGET_CREATED, outcome=AuditOutcome.SUCCESS
):
    service = AuditService(AuditRepository(db_session))
    event = service.append_event(
        event_type=event_type,
        category=AuditEventCategory.TARGET,
        outcome=outcome,
        context=AuditContext(actor=ActorContext.anonymous(), request=RequestContext()),
        resource_type=AuditResourceType.TARGET,
        resource_id=uuid.uuid4(),
        metadata={"target_type": "IPV4"},
    )
    db_session.commit()
    return event


# --- Empty database ---


def test_list_audit_events_empty_database(client: TestClient):
    response = client.get("/api/v1/audit")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["events"] == []
    assert body["data"]["total"] == 0


# --- List / retrieve ---


def test_list_audit_events_populated(client: TestClient, db_session):
    _seed_event(db_session)
    response = client.get("/api/v1/audit")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["events"][0]["event_type"] == "TARGET_CREATED"


def test_get_audit_event_by_id(client: TestClient, db_session):
    event = _seed_event(db_session)
    response = client.get(f"/api/v1/audit/{event.id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(event.id)


def test_get_audit_event_missing_returns_404(client: TestClient):
    response = client.get(f"/api/v1/audit/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_audit_event_invalid_uuid_returns_422(client: TestClient):
    response = client.get("/api/v1/audit/not-a-uuid")
    assert response.status_code == 422


# --- Filters ---


def test_filter_by_event_type(client: TestClient, db_session):
    _seed_event(db_session, event_type=AuditEventType.TARGET_CREATED)
    _seed_event(db_session, event_type=AuditEventType.TARGET_DELETED)

    response = client.get("/api/v1/audit", params={"event_type": "TARGET_DELETED"})
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["events"][0]["event_type"] == "TARGET_DELETED"


def test_filter_by_category(client: TestClient, db_session):
    _seed_event(db_session)
    response = client.get("/api/v1/audit", params={"category": "TARGET"})
    assert response.json()["data"]["total"] == 1

    response_other = client.get("/api/v1/audit", params={"category": "RISK"})
    assert response_other.json()["data"]["total"] == 0


def test_filter_by_outcome(client: TestClient, db_session):
    _seed_event(db_session, outcome=AuditOutcome.SUCCESS)
    response = client.get("/api/v1/audit", params={"outcome": "FAILURE"})
    assert response.json()["data"]["total"] == 0


def test_filter_by_invalid_event_type_rejected(client: TestClient):
    response = client.get("/api/v1/audit", params={"event_type": "NOT_REAL"})
    assert response.status_code == 422


def test_filter_by_invalid_date_range_rejected(client: TestClient):
    response = client.get("/api/v1/audit", params={"occurred_after": "not-a-date"})
    assert response.status_code == 422


# --- Pagination ---


def test_pagination_limit_and_skip(client: TestClient, db_session):
    for _ in range(5):
        _seed_event(db_session)

    response = client.get("/api/v1/audit", params={"limit": 2})
    data = response.json()["data"]
    assert len(data["events"]) == 2
    assert data["total"] == 5


def test_limit_above_maximum_rejected(client: TestClient):
    response = client.get("/api/v1/audit", params={"limit": 1000})
    assert response.status_code == 422


def test_limit_below_minimum_rejected(client: TestClient):
    response = client.get("/api/v1/audit", params={"limit": 0})
    assert response.status_code == 422


# --- Read-only surface: no create/update/delete ---


def test_post_rejected(client: TestClient):
    response = client.post("/api/v1/audit", json={})
    assert response.status_code == 405


def test_put_rejected(client: TestClient, db_session):
    event = _seed_event(db_session)
    response = client.put(f"/api/v1/audit/{event.id}", json={})
    assert response.status_code == 405


def test_patch_rejected(client: TestClient, db_session):
    event = _seed_event(db_session)
    response = client.patch(f"/api/v1/audit/{event.id}", json={})
    assert response.status_code == 405


def test_delete_rejected(client: TestClient, db_session):
    event = _seed_event(db_session)
    response = client.delete(f"/api/v1/audit/{event.id}")
    assert response.status_code == 405


# --- No sensitive/internal detail exposure ---


def test_response_never_exposes_secrets_or_internal_paths(
    client: TestClient, db_session
):
    _seed_event(db_session)
    response = client.get("/api/v1/audit")
    body = response.text.lower()
    assert "api_key" not in body
    assert "password" not in body
    assert "c:\\" not in body
    assert "database_url" not in body
