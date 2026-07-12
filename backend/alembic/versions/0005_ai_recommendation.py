"""ai_recommendation

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-13 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_recommendations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("vulnerability_id", sa.Uuid(), nullable=False),
        sa.Column("risk_assessment_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=20), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("remediation_steps", postgresql.JSONB(), nullable=False),
        sa.Column("validation_steps", postgresql.JSONB(), nullable=False),
        sa.Column("cautions", postgresql.JSONB(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["risk_assessment_id"], ["risk_assessments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["vulnerability_id"], ["vulnerabilities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "risk_assessment_id",
            "provider",
            "model",
            "prompt_version",
            name="uq_ai_recommendation_identity",
        ),
    )
    op.create_index(
        op.f("ix_ai_recommendations_id"), "ai_recommendations", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_ai_recommendations_vulnerability_id"),
        "ai_recommendations",
        ["vulnerability_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ai_recommendations_risk_assessment_id"),
        "ai_recommendations",
        ["risk_assessment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_ai_recommendations_risk_assessment_id"),
        table_name="ai_recommendations",
    )
    op.drop_index(
        op.f("ix_ai_recommendations_vulnerability_id"), table_name="ai_recommendations"
    )
    op.drop_index(op.f("ix_ai_recommendations_id"), table_name="ai_recommendations")
    op.drop_table("ai_recommendations")
