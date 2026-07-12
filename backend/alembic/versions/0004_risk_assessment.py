"""risk_assessment

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-12 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "scope",
            sa.Enum("VULNERABILITY", "ASSET", "SCAN", "ASSESSMENT", name="riskscope"),
            nullable=False,
        ),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column(
            "risk_level",
            sa.Enum(
                "INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL", name="risklevel"
            ),
            nullable=False,
        ),
        sa.Column("calculation_version", sa.String(length=20), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supporting_factors", postgresql.JSONB(), nullable=False),
        sa.Column("scan_id", sa.Uuid(), nullable=True),
        sa.Column("asset_id", sa.Uuid(), nullable=True),
        sa.Column("vulnerability_id", sa.Uuid(), nullable=True),
        sa.Column("service_id", sa.Uuid(), nullable=True),
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
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scan_id"], ["scan_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["vulnerability_id"], ["vulnerabilities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "(scope = 'VULNERABILITY' AND scan_id IS NOT NULL AND asset_id IS NOT NULL "
            "AND vulnerability_id IS NOT NULL) OR "
            "(scope = 'ASSET' AND scan_id IS NOT NULL AND asset_id IS NOT NULL "
            "AND vulnerability_id IS NULL AND service_id IS NULL) OR "
            "(scope = 'SCAN' AND scan_id IS NOT NULL AND asset_id IS NULL "
            "AND vulnerability_id IS NULL AND service_id IS NULL) OR "
            "(scope = 'ASSESSMENT' AND scan_id IS NULL AND asset_id IS NULL "
            "AND vulnerability_id IS NULL AND service_id IS NULL)",
            name="chk_risk_assessment_scope_invariants",
        ),
    )
    op.create_index(
        op.f("ix_risk_assessments_id"), "risk_assessments", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_risk_assessments_scope"), "risk_assessments", ["scope"], unique=False
    )
    op.create_index(
        op.f("ix_risk_assessments_scan_id"),
        "risk_assessments",
        ["scan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_risk_assessments_asset_id"),
        "risk_assessments",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_risk_assessments_vulnerability_id"),
        "risk_assessments",
        ["vulnerability_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_risk_assessments_service_id"),
        "risk_assessments",
        ["service_id"],
        unique=False,
    )

    op.create_index(
        "uq_risk_vulnerability_with_service",
        "risk_assessments",
        ["scan_id", "asset_id", "vulnerability_id", "service_id"],
        unique=True,
        postgresql_where=sa.text("scope = 'VULNERABILITY' AND service_id IS NOT NULL"),
    )
    op.create_index(
        "uq_risk_vulnerability_without_service",
        "risk_assessments",
        ["scan_id", "asset_id", "vulnerability_id"],
        unique=True,
        postgresql_where=sa.text("scope = 'VULNERABILITY' AND service_id IS NULL"),
    )
    op.create_index(
        "uq_risk_asset",
        "risk_assessments",
        ["scan_id", "asset_id"],
        unique=True,
        postgresql_where=sa.text("scope = 'ASSET'"),
    )
    op.create_index(
        "uq_risk_scan",
        "risk_assessments",
        ["scan_id"],
        unique=True,
        postgresql_where=sa.text("scope = 'SCAN'"),
    )
    op.create_index(
        "uq_risk_assessment_singleton",
        "risk_assessments",
        ["scope"],
        unique=True,
        postgresql_where=sa.text("scope = 'ASSESSMENT'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_risk_assessment_singleton",
        table_name="risk_assessments",
        postgresql_where=sa.text("scope = 'ASSESSMENT'"),
    )
    op.drop_index(
        "uq_risk_scan",
        table_name="risk_assessments",
        postgresql_where=sa.text("scope = 'SCAN'"),
    )
    op.drop_index(
        "uq_risk_asset",
        table_name="risk_assessments",
        postgresql_where=sa.text("scope = 'ASSET'"),
    )
    op.drop_index(
        "uq_risk_vulnerability_without_service",
        table_name="risk_assessments",
        postgresql_where=sa.text("scope = 'VULNERABILITY' AND service_id IS NULL"),
    )
    op.drop_index(
        "uq_risk_vulnerability_with_service",
        table_name="risk_assessments",
        postgresql_where=sa.text("scope = 'VULNERABILITY' AND service_id IS NOT NULL"),
    )

    op.drop_index(op.f("ix_risk_assessments_service_id"), table_name="risk_assessments")
    op.drop_index(
        op.f("ix_risk_assessments_vulnerability_id"), table_name="risk_assessments"
    )
    op.drop_index(op.f("ix_risk_assessments_asset_id"), table_name="risk_assessments")
    op.drop_index(op.f("ix_risk_assessments_scan_id"), table_name="risk_assessments")
    op.drop_index(op.f("ix_risk_assessments_scope"), table_name="risk_assessments")
    op.drop_index(op.f("ix_risk_assessments_id"), table_name="risk_assessments")
    op.drop_table("risk_assessments")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="risklevel").drop(bind, checkfirst=True)
        sa.Enum(name="riskscope").drop(bind, checkfirst=True)
