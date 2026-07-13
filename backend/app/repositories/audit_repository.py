import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import (
    AuditActorType,
    AuditEventCategory,
    AuditEventType,
    AuditOutcome,
    AuditResourceType,
)
from app.models.audit_event import AuditEvent


class AuditRepository:
    """Append-only repository for AuditEvent persistence.

    Deliberately exposes no update(), delete(), or upsert() method for
    persisted events. `append()` only adds and flushes — it never commits;
    the calling service owns the transaction boundary so that SUCCESS/
    FAILURE audit semantics can be coordinated with the business
    transaction they document (see AuditService and each integrated
    service's transaction semantics).
    """

    def __init__(self, session: Session):
        self.session = session

    def append(self, event: AuditEvent) -> AuditEvent:
        """Persist a new audit event. Never updates an existing row."""
        self.session.add(event)
        self.session.flush()
        return event

    def get_by_id(self, event_id: uuid.UUID) -> AuditEvent | None:
        stmt = select(AuditEvent).where(AuditEvent.id == event_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list(
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
        """Retrieve a paginated, filtered list of audit events.

        Ordered deterministically by occurred_at descending, id descending
        as a tie-breaker for events recorded within the same instant.
        """
        stmt = select(AuditEvent)
        count_stmt = select(func.count(AuditEvent.id))

        filters = []
        if event_type is not None:
            filters.append(AuditEvent.event_type == event_type)
        if category is not None:
            filters.append(AuditEvent.category == category)
        if outcome is not None:
            filters.append(AuditEvent.outcome == outcome)
        if resource_type is not None:
            filters.append(AuditEvent.resource_type == resource_type)
        if resource_id is not None:
            filters.append(AuditEvent.resource_id == resource_id)
        if scan_id is not None:
            filters.append(AuditEvent.scan_id == scan_id)
        if actor_type is not None:
            filters.append(AuditEvent.actor_type == actor_type)
        if occurred_after is not None:
            filters.append(AuditEvent.occurred_at >= occurred_after)
        if occurred_before is not None:
            filters.append(AuditEvent.occurred_at <= occurred_before)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = self.session.execute(count_stmt).scalar() or 0

        stmt = (
            stmt.order_by(AuditEvent.occurred_at.desc(), AuditEvent.id.desc())
            .offset(skip)
            .limit(limit)
        )
        items = self.session.execute(stmt).scalars().all()

        return items, total
