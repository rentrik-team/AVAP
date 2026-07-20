"""scan_cancellation_and_output

Enables background scan execution with cancellation support:

- scan_jobs previously had no way to be stopped mid-execution and no
  columns to retain raw scanner output, so a running scan's progress was
  never observable and could not be recovered after a timeout/cancel.
- Adds the CANCELLED value to the scanstatus enum (Nmap/OpenVAS scans can
  now be cancelled by the user while running).
- Adds output_file_path/stdout_log/stderr_log to scan_jobs so partial
  results are retained even when a scan is cancelled or times out.

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-17 09:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside the migration's normal
    # transaction block on PostgreSQL; autocommit_block() ends the
    # transaction for the duration of this statement.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE scanstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")

    op.add_column(
        "scan_jobs",
        sa.Column("output_file_path", sa.String(length=1024), nullable=True),
    )
    op.add_column("scan_jobs", sa.Column("stdout_log", sa.Text(), nullable=True))
    op.add_column("scan_jobs", sa.Column("stderr_log", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("scan_jobs", "stderr_log")
    op.drop_column("scan_jobs", "stdout_log")
    op.drop_column("scan_jobs", "output_file_path")

    # PostgreSQL does not support removing an enum value directly; rebuild
    # the type without CANCELLED, and switch any such rows to FAILED first
    # so the column conversion below does not fail.
    with op.get_context().autocommit_block():
        op.execute(
            "UPDATE scan_jobs SET status = 'FAILED' WHERE status = 'CANCELLED'"
        )
        op.execute("ALTER TYPE scanstatus RENAME TO scanstatus_old")
        op.execute(
            "CREATE TYPE scanstatus AS ENUM "
            "('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')"
        )
        op.execute(
            "ALTER TABLE scan_jobs ALTER COLUMN status TYPE scanstatus "
            "USING status::text::scanstatus"
        )
        op.execute("DROP TYPE scanstatus_old")
