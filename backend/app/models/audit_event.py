import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.enums import (
    AuditActorType,
    AuditEventCategory,
    AuditEventType,
    AuditOutcome,
    AuditResourceType,
)
from app.database.base import Base, TimestampMixin

# Portable JSON type: renders as JSONB on PostgreSQL, plain JSON on SQLite (tests).
AuditMetadataType = JSONB().with_variant(JSON(), "sqlite")


class AuditEvent(Base, TimestampMixin):
    """Append-only record of a security-relevant business action.

    Application code must never update or delete a persisted AuditEvent.
    `resource_id`/`scan_id` are plain UUID columns with no foreign key:
    audit evidence must survive deletion of the resource it documents. On
    PostgreSQL, migration 0007 additionally installs a trigger that rejects
    UPDATE/DELETE at the database level; see modules_docs/10_audit_logging.md
    for the exact guarantee level (SQLite test runs do not get this
    database-level enforcement, only the application-level one).
    """

    __tablename__ = "audit_events"

    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType, name="auditeventtype"), nullable=False, index=True
    )

    category: Mapped[AuditEventCategory] = mapped_column(
        Enum(AuditEventCategory, name="auditeventcategory"), nullable=False, index=True
    )

    outcome: Mapped[AuditOutcome] = mapped_column(
        Enum(AuditOutcome, name="auditoutcome"), nullable=False, index=True
    )

    actor_type: Mapped[AuditActorType] = mapped_column(
        Enum(AuditActorType, name="auditactortype"), nullable=False
    )

    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    resource_type: Mapped[AuditResourceType | None] = mapped_column(
        Enum(AuditResourceType, name="auditresourcetype"), nullable=True, index=True
    )

    # Intentionally not a ForeignKey: audit evidence must survive deletion
    # of the referenced resource.
    resource_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)

    # Intentionally not a ForeignKey, for the same reason; kept separate
    # from resource_id so scan-scoped queries do not depend on which
    # resource_type happens to represent "the scan" for a given event.
    scan_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)

    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    source_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        AuditMetadataType, nullable=False, default=dict
    )

    # The business timestamp ("when did this occur"), distinct from the
    # generic created_at/updated_at bookkeeping columns inherited from
    # TimestampMixin — the same pattern used by RiskAssessment.calculated_at,
    # AIRecommendation.generated_at, and Report.generated_at. Always
    # server-generated; never accepted from an API caller.
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    __table_args__ = (Index("ix_audit_events_occurred_at_id", "occurred_at", "id"),)
