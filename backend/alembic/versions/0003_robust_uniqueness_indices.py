"""robust_uniqueness_indices

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-12 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add unique index for NULL CVE on vulnerabilities table
    op.create_index(
        'uq_vulnerabilities_name_cve_null',
        'vulnerabilities',
        ['name'],
        unique=True,
        where=sa.text('cve IS NULL')
    )

    # 2. Add unique indexes for scan_findings table to handle nullable columns
    op.create_index(
        'uq_scan_findings_null_vuln',
        'scan_findings',
        ['scan_id', 'asset_id', 'service_id'],
        unique=True,
        where=sa.text('vulnerability_id IS NULL AND service_id IS NOT NULL')
    )
    op.create_index(
        'uq_scan_findings_null_service',
        'scan_findings',
        ['scan_id', 'asset_id', 'vulnerability_id'],
        unique=True,
        where=sa.text('vulnerability_id IS NOT NULL AND service_id IS NULL')
    )
    op.create_index(
        'uq_scan_findings_both_null',
        'scan_findings',
        ['scan_id', 'asset_id'],
        unique=True,
        where=sa.text('vulnerability_id IS NULL AND service_id IS NULL')
    )


def downgrade() -> None:
    # Drop scan_findings partial indexes
    op.drop_index('uq_scan_findings_both_null', table_name='scan_findings', where=sa.text('vulnerability_id IS NULL AND service_id IS NULL'))
    op.drop_index('uq_scan_findings_null_service', table_name='scan_findings', where=sa.text('vulnerability_id IS NOT NULL AND service_id IS NULL'))
    op.drop_index('uq_scan_findings_null_vuln', table_name='scan_findings', where=sa.text('vulnerability_id IS NULL AND service_id IS NOT NULL'))

    # Drop vulnerabilities partial index
    op.drop_index('uq_vulnerabilities_name_cve_null', table_name='vulnerabilities', where=sa.text('cve IS NULL'))
