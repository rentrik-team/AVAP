"""report

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-14 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scan_id", sa.Uuid(), nullable=False),
        sa.Column("format", sa.String(length=10), nullable=False),
        sa.Column("report_template_version", sa.String(length=20), nullable=False),
        sa.Column("risk_calculation_version", sa.String(length=20), nullable=False),
        sa.Column(
            "source_risk_calculated_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("overall_risk_score", sa.Float(), nullable=False),
        # Reuses the existing 'risklevel' Postgres enum type created by migration
        # 0004; create_type=False avoids attempting to recreate it.
        sa.Column(
            "overall_risk_level",
            postgresql.ENUM(
                "INFORMATIONAL",
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
                name="risklevel",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("vulnerability_count", sa.Integer(), nullable=False),
        sa.Column("ai_recommendations_included", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["scan_id"], ["scan_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "scan_id", "generated_at", name="uq_reports_scan_generated_at"
        ),
    )
    op.create_index(op.f("ix_reports_id"), "reports", ["id"], unique=False)
    op.create_index(op.f("ix_reports_scan_id"), "reports", ["scan_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reports_scan_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_id"), table_name="reports")
    op.drop_table("reports")
