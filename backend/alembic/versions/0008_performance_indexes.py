"""performance_indexes

Backend Hardening & Stabilization phase: index review findings.

- scan_jobs.target_id had no index despite being an active foreign key
  queried on every scan-creation duplicate-running-scan check
  (ScanRepository.get_running_scans_for_target) — every other foreign key
  in the schema is indexed; this was an oversight.
- targets, scan_jobs, assets, and vulnerabilities are all listed via
  `ORDER BY created_at DESC` with pagination (every primary list endpoint);
  risk_assessments is listed via `ORDER BY calculated_at DESC`. None of
  these sort columns were indexed, forcing a full-table sort on every
  paginated list request.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-14 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        op.f("ix_scan_jobs_target_id"), "scan_jobs", ["target_id"], unique=False
    )
    op.create_index(
        op.f("ix_targets_created_at"), "targets", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_scan_jobs_created_at"), "scan_jobs", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_assets_created_at"), "assets", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_vulnerabilities_created_at"),
        "vulnerabilities",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_risk_assessments_calculated_at"),
        "risk_assessments",
        ["calculated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_risk_assessments_calculated_at"), table_name="risk_assessments"
    )
    op.drop_index(op.f("ix_vulnerabilities_created_at"), table_name="vulnerabilities")
    op.drop_index(op.f("ix_assets_created_at"), table_name="assets")
    op.drop_index(op.f("ix_scan_jobs_created_at"), table_name="scan_jobs")
    op.drop_index(op.f("ix_targets_created_at"), table_name="targets")
    op.drop_index(op.f("ix_scan_jobs_target_id"), table_name="scan_jobs")
