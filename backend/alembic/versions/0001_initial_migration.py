"""initial_migration

Revision ID: 0001
Revises: 
Create Date: 2026-07-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'targets',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('target', sa.String(length=253), nullable=False),
        sa.Column('target_type', sa.Enum('IPV4', 'CIDR', 'HOSTNAME', name='targettype'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_targets_id'), 'targets', ['id'], unique=False)
    op.create_index(op.f('ix_targets_target'), 'targets', ['target'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_targets_target'), table_name='targets')
    op.drop_index(op.f('ix_targets_id'), table_name='targets')
    op.drop_table('targets')
