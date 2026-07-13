"""scan_management_and_inventory

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-11 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create scan_jobs table (from Module 02, missing migration)
    op.create_table(
        "scan_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "RUNNING", "COMPLETED", "FAILED", name="scanstatus"),
            nullable=False,
        ),
        sa.Column("scan_type", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_duration", sa.Float(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["target_id"], ["targets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scan_jobs_id"), "scan_jobs", ["id"], unique=False)

    # 2. Create assets table
    op.create_table(
        "assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ipv4", sa.String(length=45), nullable=False),
        sa.Column("hostname", sa.String(length=253), nullable=True),
        sa.Column("operating_system", sa.String(length=253), nullable=True),
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
    op.create_index(op.f("ix_assets_id"), "assets", ["id"], unique=False)
    op.create_index(op.f("ix_assets_ipv4"), "assets", ["ipv4"], unique=True)

    # 3. Create services table
    op.create_table(
        "services",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("protocol", sa.String(length=10), nullable=False),
        sa.Column("service_name", sa.String(length=50), nullable=False),
        sa.Column("product", sa.String(length=100), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("extra_info", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "asset_id", "port", "protocol", name="uq_services_asset_port_proto"
        ),
    )
    op.create_index(op.f("ix_services_id"), "services", ["id"], unique=False)
    op.create_index(
        op.f("ix_services_asset_id"), "services", ["asset_id"], unique=False
    )

    # 4. Create vulnerabilities table
    op.create_table(
        "vulnerabilities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("severity_score", sa.Float(), nullable=False),
        sa.Column("severity_rating", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cve", sa.String(length=20), nullable=True),
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
        sa.UniqueConstraint("name", "cve", name="uq_vulnerabilities_name_cve"),
    )
    op.create_index(
        op.f("ix_vulnerabilities_id"), "vulnerabilities", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_vulnerabilities_cve"), "vulnerabilities", ["cve"], unique=False
    )

    # 5. Create scan_findings table
    op.create_table(
        "scan_findings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scan_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
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
        sa.UniqueConstraint(
            "scan_id",
            "asset_id",
            "vulnerability_id",
            "service_id",
            name="uq_scan_findings_composite",
        ),
    )
    op.create_index(op.f("ix_scan_findings_id"), "scan_findings", ["id"], unique=False)
    op.create_index(
        op.f("ix_scan_findings_scan_id"), "scan_findings", ["scan_id"], unique=False
    )
    op.create_index(
        op.f("ix_scan_findings_asset_id"), "scan_findings", ["asset_id"], unique=False
    )
    op.create_index(
        op.f("ix_scan_findings_vulnerability_id"),
        "scan_findings",
        ["vulnerability_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scan_findings_service_id"),
        "scan_findings",
        ["service_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_scan_findings_service_id"), table_name="scan_findings")
    op.drop_index(op.f("ix_scan_findings_vulnerability_id"), table_name="scan_findings")
    op.drop_index(op.f("ix_scan_findings_asset_id"), table_name="scan_findings")
    op.drop_index(op.f("ix_scan_findings_scan_id"), table_name="scan_findings")
    op.drop_index(op.f("ix_scan_findings_id"), table_name="scan_findings")
    op.drop_table("scan_findings")

    op.drop_index(op.f("ix_vulnerabilities_cve"), table_name="vulnerabilities")
    op.drop_index(op.f("ix_vulnerabilities_id"), table_name="vulnerabilities")
    op.drop_table("vulnerabilities")

    op.drop_index(op.f("ix_services_asset_id"), table_name="services")
    op.drop_index(op.f("ix_services_id"), table_name="services")
    op.drop_table("services")

    op.drop_index(op.f("ix_assets_ipv4"), table_name="assets")
    op.drop_index(op.f("ix_assets_id"), table_name="assets")
    op.drop_table("assets")

    op.drop_index(op.f("ix_scan_jobs_id"), table_name="scan_jobs")
    op.drop_table("scan_jobs")

    # Drop enum scanstatus
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="scanstatus").drop(bind, checkfirst=True)
