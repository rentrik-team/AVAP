"""scan_completion_audit_events

The background scan execution added in 0009 emits SCAN_COMPLETED,
SCAN_FAILED, and SCAN_CANCELLED audit events when a scan job finishes, but
those values were never added to the auditeventtype Postgres enum —
writing one fails with InvalidTextRepresentation, which rolls back the
whole finalization transaction and leaves the scan job stuck at RUNNING
forever (discovered by actually running a scan end-to-end).

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-17 17:10:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS 'SCAN_COMPLETED'")
        op.execute("ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS 'SCAN_FAILED'")
        op.execute("ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS 'SCAN_CANCELLED'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly; rebuild
    # the type without them. Any audit_events row already using one of
    # these values would violate the narrower type, but audit events are
    # never deleted/rewritten by application code, so this only matters
    # for a downgrade in an environment that never wrote one.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE auditeventtype RENAME TO auditeventtype_old")
        op.execute(
            """
            CREATE TYPE auditeventtype AS ENUM (
                'TARGET_CREATED', 'TARGET_UPDATED', 'TARGET_DELETED',
                'SCAN_CREATED', 'SCAN_DELETED',
                'INVENTORY_PROCESSED', 'INVENTORY_PROCESSING_FAILED',
                'RISK_CALCULATION_COMPLETED', 'RISK_CALCULATION_FAILED',
                'AI_RECOMMENDATION_GENERATED', 'AI_RECOMMENDATION_FAILED',
                'REPORT_GENERATED', 'REPORT_GENERATION_FAILED',
                'REPORT_DOWNLOADED', 'REPORT_DELETED'
            )
            """
        )
        op.execute(
            "ALTER TABLE audit_events ALTER COLUMN event_type TYPE auditeventtype "
            "USING event_type::text::auditeventtype"
        )
        op.execute("DROP TYPE auditeventtype_old")
