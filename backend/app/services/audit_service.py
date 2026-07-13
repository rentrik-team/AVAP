import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.audit.context import AuditContext
from app.audit.metadata_policy import validate_metadata
from app.core.enums import (
    AuditActorType,
    AuditEventCategory,
    AuditEventType,
    AuditOutcome,
    AuditResourceType,
)
from app.core.exceptions import NotFoundException
from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository

logger = logging.getLogger(__name__)


class AuditService:
    """Business logic for recording and retrieving audit events.

    `append_event` never commits — it adds and flushes the new
    `AuditEvent` onto the caller's existing session so the calling service
    controls whether it lands in the same transaction as the business
    action it documents (SUCCESS) or in a fresh transaction after a
    business rollback (FAILURE). See modules_docs/10_audit_logging.md for
    the exact transaction semantics guarantee.

    AuditService never audits its own operations (no recursive auditing),
    never calls another business service, and never influences business
    logic — it is purely an accountability record.
    """

    def __init__(self, audit_repository: AuditRepository):
        self.audit_repository = audit_repository

    def append_event(
        self,
        event_type: AuditEventType,
        category: AuditEventCategory,
        outcome: AuditOutcome,
        context: AuditContext,
        resource_type: AuditResourceType | None = None,
        resource_id: uuid.UUID | None = None,
        scan_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> AuditEvent:
        """Append one audit event. Raises UnsafeAuditMetadataException if
        `metadata` violates the audit metadata safety policy — the event is
        never persisted with unsafe metadata, and is never silently
        redacted instead of rejected.
        """
        safe_metadata = validate_metadata(metadata)

        event = AuditEvent(
            event_type=event_type,
            category=category,
            outcome=outcome,
            actor_type=context.actor.actor_type,
            actor_id=context.actor.actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            scan_id=scan_id,
            request_id=context.request.request_id,
            source_ip=context.request.source_ip,
            event_metadata=safe_metadata,
            occurred_at=datetime.now(UTC),
        )
        return self.audit_repository.append(event)

    def record_failure_safely(
        self,
        session: Session,
        event_type: AuditEventType,
        category: AuditEventCategory,
        context: AuditContext,
        resource_type: AuditResourceType | None = None,
        resource_id: uuid.UUID | None = None,
        scan_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Best-effort durable persistence of a FAILURE audit event after a
        business rollback, in its own fresh transaction on `session`.

        This method never raises: if audit persistence itself fails here,
        the sanitized failure is recorded via structured logging only, and
        the caller must proceed to raise its own original business
        exception unchanged. This is the documented audit failure policy
        for failure events — never replace or mask the real error with an
        audit-subsystem error, and never leave the caller's transaction in
        an inconsistent state.
        """
        try:
            self.append_event(
                event_type=event_type,
                category=category,
                outcome=AuditOutcome.FAILURE,
                context=context,
                resource_type=resource_type,
                resource_id=resource_id,
                scan_id=scan_id,
                metadata=metadata,
            )
            session.commit()
        except Exception:
            session.rollback()
            logger.error(
                "Audit subsystem failed to record a FAILURE event; the "
                "original business failure is unaffected.",
                extra={"event_type": event_type.value},
                exc_info=True,
            )

    def get_event(self, event_id: uuid.UUID) -> AuditEvent:
        event = self.audit_repository.get_by_id(event_id)
        if not event:
            raise NotFoundException(f"Audit event {event_id} not found.")
        return event

    def list_events(
        self,
        skip: int = 0,
        limit: int = 50,
        event_type: AuditEventType | None = None,
        category: AuditEventCategory | None = None,
        outcome: AuditOutcome | None = None,
        resource_type: AuditResourceType | None = None,
        resource_id: uuid.UUID | None = None,
        scan_id: uuid.UUID | None = None,
        actor_type: AuditActorType | None = None,
        occurred_after: datetime | None = None,
        occurred_before: datetime | None = None,
    ) -> tuple[Sequence[AuditEvent], int]:
        return self.audit_repository.list(
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
