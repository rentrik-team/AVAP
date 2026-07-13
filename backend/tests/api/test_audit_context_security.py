"""Security tests for Module 10's request-correlation middleware and actor
resolution: request IDs must be bounded/safe, forwarded IP headers must
never be trusted, and no client-supplied header can impersonate an actor
identity. Exercised through the real HTTP stack (client fixture), not unit
calls to the middleware function.
"""

import uuid

from fastapi.testclient import TestClient

from app.core.enums import AuditActorType


def _create_target(client: TestClient, ip="203.0.113.200", **headers):
    return client.post("/api/v1/targets", json={"target": ip}, headers=headers or None)


def _latest_target_created_event(client: TestClient):
    response = client.get(
        "/api/v1/audit", params={"event_type": "TARGET_CREATED", "limit": 1}
    )
    return response.json()["data"]["events"][0]


# --- Request ID: generated when absent, valid inbound reused, invalid replaced ---


def test_request_id_generated_when_absent(client: TestClient):
    response = _create_target(client, ip="203.0.113.201")
    assert response.status_code == 201
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0

    event = _latest_target_created_event(client)
    assert event["request_id"] == response.headers["X-Request-ID"]


def test_valid_inbound_request_id_is_reused(client: TestClient):
    inbound_id = "client-supplied-id-123"
    response = _create_target(
        client, ip="203.0.113.202", **{"X-Request-ID": inbound_id}
    )
    assert response.headers["X-Request-ID"] == inbound_id

    event = _latest_target_created_event(client)
    assert event["request_id"] == inbound_id


def test_oversized_request_id_is_replaced(client: TestClient):
    oversized = "a" * 500
    response = _create_target(client, ip="203.0.113.203", **{"X-Request-ID": oversized})
    assert response.headers["X-Request-ID"] != oversized
    assert len(response.headers["X-Request-ID"]) <= 100


def test_control_character_request_id_is_replaced(client: TestClient):
    malformed = "abc\r\ndef"
    response = _create_target(client, ip="203.0.113.204", **{"X-Request-ID": malformed})
    assert response.headers["X-Request-ID"] != malformed
    # Confirm it fell back to a generated UUID.
    uuid.UUID(response.headers["X-Request-ID"])


def test_malformed_symbols_request_id_is_replaced(client: TestClient):
    malformed = "id with spaces & symbols!"
    response = _create_target(client, ip="203.0.113.205", **{"X-Request-ID": malformed})
    assert response.headers["X-Request-ID"] != malformed


# --- Client IP / actor: forwarded headers never trusted, no impersonation ---


def test_forwarded_for_header_does_not_change_recorded_source_ip(client: TestClient):
    _create_target(client, ip="203.0.113.206")
    direct_event = _latest_target_created_event(client)

    _create_target(client, ip="203.0.113.207", **{"X-Forwarded-For": "1.2.3.4"})
    spoofed_event = _latest_target_created_event(client)

    # Both requests come from the same TestClient connection; the forwarded
    # header must not change what gets recorded.
    assert spoofed_event["source_ip"] == direct_event["source_ip"]
    assert spoofed_event["source_ip"] != "1.2.3.4"


def test_real_ip_header_does_not_change_recorded_source_ip(client: TestClient):
    _create_target(client, ip="203.0.113.208", **{"X-Real-IP": "9.9.9.9"})
    event = _latest_target_created_event(client)
    assert event["source_ip"] != "9.9.9.9"


def test_actor_impersonation_headers_are_ignored(client: TestClient):
    response = _create_target(
        client,
        ip="203.0.113.209",
        **{"X-User": "admin", "X-Username": "root", "X-Actor-ID": "superuser"},
    )
    assert response.status_code == 201
    event = _latest_target_created_event(client)
    assert event["actor_type"] == AuditActorType.ANONYMOUS.value
    assert event["actor_id"] is None
