"""audit event

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-13 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TRIGGER_FUNCTION = "audit_events_block_mutation"
_TRIGGER_NAME = "audit_events_no_update_delete"


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "TARGET_CREATED",
                "TARGET_UPDATED",
                "TARGET_DELETED",
                "SCAN_CREATED",
                "SCAN_DELETED",
                "INVENTORY_PROCESSED",
                "INVENTORY_PROCESSING_FAILED",
                "RISK_CALCULATION_COMPLETED",
                "RISK_CALCULATION_FAILED",
                "AI_RECOMMENDATION_GENERATED",
                "AI_RECOMMENDATION_FAILED",
                "REPORT_GENERATED",
                "REPORT_GENERATION_FAILED",
                "REPORT_DOWNLOADED",
                "REPORT_DELETED",
                name="auditeventtype",
            ),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "SYSTEM",
                "TARGET",
                "SCAN",
                "INVENTORY",
                "RISK",
                "AI",
                "REPORT",
                name="auditeventcategory",
            ),
            nullable=False,
        ),
        sa.Column(
            "outcome",
            sa.Enum("SUCCESS", "FAILURE", name="auditoutcome"),
            nullable=False,
        ),
        sa.Column(
            "actor_type",
            sa.Enum("SYSTEM", "ANONYMOUS", name="auditactortype"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.String(length=100), nullable=True),
        sa.Column(
            "resource_type",
            sa.Enum(
                "TARGET",
                "SCAN",
                "RISK_ASSESSMENT",
                "AI_RECOMMENDATION",
                "REPORT",
                name="auditresourcetype",
            ),
            nullable=True,
        ),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("scan_id", sa.Uuid(), nullable=True),
        sa.Column("request_id", sa.String(length=100), nullable=True),
        sa.Column("source_ip", sa.String(length=45), nullable=True),
        sa.Column("event_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_events_id"), "audit_events", ["id"], unique=False)
    op.create_index(
        op.f("ix_audit_events_event_type"), "audit_events", ["event_type"], unique=False
    )
    op.create_index(
        op.f("ix_audit_events_category"), "audit_events", ["category"], unique=False
    )
    op.create_index(
        op.f("ix_audit_events_outcome"), "audit_events", ["outcome"], unique=False
    )
    op.create_index(
        op.f("ix_audit_events_resource_type"),
        "audit_events",
        ["resource_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_events_resource_id"),
        "audit_events",
        ["resource_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_events_scan_id"), "audit_events", ["scan_id"], unique=False
    )
    op.create_index(
        op.f("ix_audit_events_occurred_at"),
        "audit_events",
        ["occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_occurred_at_id",
        "audit_events",
        ["occurred_at", "id"],
        unique=False,
    )

    # Database-level append-only enforcement (PostgreSQL only). Audit rows
    # may only ever be inserted; any UPDATE or DELETE attempt is rejected by
    # the database itself, independent of application code correctness.
    # SQLite (used by the automated test suite) has no equivalent portable
    # trigger mechanism here, so this guarantee is verified by offline SQL
    # compilation/manual review rather than by the pytest suite.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            f"""
            CREATE FUNCTION {_TRIGGER_FUNCTION}() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION
                    'audit_events rows are append-only and cannot be % (id=%)',
                    TG_OP, OLD.id;
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        op.execute(
            f"""
            CREATE TRIGGER {_TRIGGER_NAME}
            BEFORE UPDATE OR DELETE ON audit_events
            FOR EACH ROW EXECUTE FUNCTION {_TRIGGER_FUNCTION}();
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(f"DROP TRIGGER IF EXISTS {_TRIGGER_NAME} ON audit_events;")
        op.execute(f"DROP FUNCTION IF EXISTS {_TRIGGER_FUNCTION}();")

    op.drop_index("ix_audit_events_occurred_at_id", table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_occurred_at"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_scan_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_resource_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_resource_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_outcome"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_category"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_event_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_id"), table_name="audit_events")
    op.drop_table("audit_events")
    sa.Enum(name="auditresourcetype").drop(bind, checkfirst=True)
    sa.Enum(name="auditactortype").drop(bind, checkfirst=True)
    sa.Enum(name="auditoutcome").drop(bind, checkfirst=True)
    sa.Enum(name="auditeventcategory").drop(bind, checkfirst=True)
    sa.Enum(name="auditeventtype").drop(bind, checkfirst=True)
