import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.core.enums import (
    AuditActorType,
    AuditEventCategory,
    AuditEventType,
    AuditOutcome,
    AuditResourceType,
)


class AuditEventResponse(BaseModel):
    """Response model for a persisted, immutable audit event.

    Represents a read-only resource: there is no corresponding
    create/update request schema, since audit events are never created or
    modified through the API.
    """

    id: uuid.UUID
    event_type: AuditEventType
    category: AuditEventCategory
    outcome: AuditOutcome
    actor_type: AuditActorType
    actor_id: str | None = None
    resource_type: AuditResourceType | None = None
    resource_id: uuid.UUID | None = None
    scan_id: uuid.UUID | None = None
    request_id: str | None = None
    source_ip: str | None = None
    event_metadata: dict[str, Any]
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventListResponse(BaseModel):
    """Response model for a paginated list of audit events."""

    events: list[AuditEventResponse]
    total: int
