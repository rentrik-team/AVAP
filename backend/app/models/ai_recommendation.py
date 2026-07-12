import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base, TimestampMixin

# Portable JSON type: renders as JSONB on PostgreSQL, plain JSON on SQLite (tests).
StepListType = JSONB().with_variant(JSON(), "sqlite")


class AIRecommendation(Base, TimestampMixin):
    """Database model for AI-generated, advisory remediation recommendations.

    A recommendation is always generated in the context of exactly one
    vulnerability-scoped RiskAssessment. This is enforced by the service
    layer (a database CHECK constraint cannot portably validate the scope
    of a row in a different table). The unique constraint below makes
    regeneration with an unchanged provider/model/prompt_version an
    in-place update rather than a duplicate insert.
    """

    __tablename__ = "ai_recommendations"

    vulnerability_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vulnerabilities.id", ondelete="CASCADE"), nullable=False, index=True
    )

    risk_assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False)

    model: Mapped[str] = mapped_column(String(100), nullable=False)

    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)

    summary: Mapped[str] = mapped_column(Text, nullable=False)

    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    remediation_steps: Mapped[list[str]] = mapped_column(StepListType, nullable=False)

    validation_steps: Mapped[list[str]] = mapped_column(
        StepListType, nullable=False, default=list
    )

    cautions: Mapped[list[str]] = mapped_column(
        StepListType, nullable=False, default=list
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships (read-only association; owning models are never modified).
    vulnerability = relationship("Vulnerability")
    risk_assessment = relationship("RiskAssessment")

    __table_args__ = (
        UniqueConstraint(
            "risk_assessment_id",
            "provider",
            "model",
            "prompt_version",
            name="uq_ai_recommendation_identity",
        ),
    )
