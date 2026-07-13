import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.audit import get_audit_service
from app.api.responses.api_response import SuccessResponse
from app.core.enums import (
    AuditActorType,
    AuditEventCategory,
    AuditEventType,
    AuditOutcome,
    AuditResourceType,
)
from app.schemas.audit import AuditEventListResponse, AuditEventResponse
from app.services.audit_service import AuditService

router = APIRouter()


@router.get(
    "",
    response_model=SuccessResponse[AuditEventListResponse],
    summary="List audit events",
)
def list_audit_events(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    event_type: AuditEventType | None = Query(None, description="Filter by event type"),
    category: AuditEventCategory | None = Query(None, description="Filter by category"),
    outcome: AuditOutcome | None = Query(None, description="Filter by outcome"),
    resource_type: AuditResourceType | None = Query(
        None, description="Filter by resource type"
    ),
    resource_id: uuid.UUID | None = Query(None, description="Filter by resource ID"),
    scan_id: uuid.UUID | None = Query(None, description="Filter by scan ID"),
    actor_type: AuditActorType | None = Query(None, description="Filter by actor type"),
    occurred_after: datetime | None = Query(
        None, description="Only events at or after this UTC timestamp"
    ),
    occurred_before: datetime | None = Query(
        None, description="Only events at or before this UTC timestamp"
    ),
    service: AuditService = Depends(get_audit_service),
) -> dict:
    """Retrieve a paginated, filtered, read-only list of audit events."""
    items, total = service.list_events(
        skip=skip,
        limit=limit,
        event_type=event_type,
        category=category,
        outcome=outcome,
        resource_type=resource_type,
        resource_id=resource_id,
        scan_id=scan_id,
        actor_type=actor_type,
        occurred_after=occurred_after,
        occurred_before=occurred_before,
    )
    responses = [AuditEventResponse.model_validate(item) for item in items]
    return {"data": AuditEventListResponse(events=responses, total=total)}


@router.get(
    "/{event_id}",
    response_model=SuccessResponse[AuditEventResponse],
    summary="Get a single audit event",
)
def get_audit_event(
    event_id: uuid.UUID,
    service: AuditService = Depends(get_audit_service),
) -> dict:
    """Retrieve one audit event by ID. Audit events are immutable; there is
    no corresponding create, update, or delete endpoint."""
    event = service.get_event(event_id)
    return {"data": AuditEventResponse.model_validate(event)}
