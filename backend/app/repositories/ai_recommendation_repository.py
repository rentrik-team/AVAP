import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_recommendation import AIRecommendation


class AIRecommendationRepository:
    """Repository for managing AIRecommendation database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, recommendation_id: uuid.UUID) -> AIRecommendation | None:
        """Retrieve a recommendation by its ID."""
        stmt = select(AIRecommendation).where(AIRecommendation.id == recommendation_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def find_identity_record(
        self,
        risk_assessment_id: uuid.UUID,
        provider: str,
        model: str,
        prompt_version: str,
    ) -> AIRecommendation | None:
        """Locate the single authoritative recommendation for an identity."""
        stmt = select(AIRecommendation).where(
            AIRecommendation.risk_assessment_id == risk_assessment_id,
            AIRecommendation.provider == provider,
            AIRecommendation.model == model,
            AIRecommendation.prompt_version == prompt_version,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_risk_assessment(
        self, risk_assessment_id: uuid.UUID
    ) -> AIRecommendation | None:
        """Retrieve the most recently generated recommendation for a risk assessment."""
        stmt = (
            select(AIRecommendation)
            .where(AIRecommendation.risk_assessment_id == risk_assessment_id)
            .order_by(AIRecommendation.generated_at.desc())
        )
        return self.session.execute(stmt).scalars().first()

    def get_by_vulnerability(
        self, vulnerability_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> tuple[Sequence[AIRecommendation], int]:
        """Retrieve the paginated recommendation history for one vulnerability."""
        stmt = select(AIRecommendation).where(
            AIRecommendation.vulnerability_id == vulnerability_id
        )
        count_stmt = select(func.count(AIRecommendation.id)).where(
            AIRecommendation.vulnerability_id == vulnerability_id
        )

        total = self.session.execute(count_stmt).scalar() or 0
        stmt = (
            stmt.offset(skip)
            .limit(limit)
            .order_by(AIRecommendation.generated_at.desc())
        )
        items = self.session.execute(stmt).scalars().all()

        return items, total

    def upsert(
        self,
        vulnerability_id: uuid.UUID,
        risk_assessment_id: uuid.UUID,
        provider: str,
        model: str,
        prompt_version: str,
        summary: str,
        explanation: str,
        remediation_steps: list[str],
        validation_steps: list[str],
        cautions: list[str],
        generated_at: datetime,
    ) -> AIRecommendation:
        """Create or update the authoritative recommendation for an identity.

        Regeneration with an unchanged provider/model/prompt_version updates
        the existing row in place rather than inserting a duplicate.
        """
        existing = self.find_identity_record(
            risk_assessment_id=risk_assessment_id,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
        )

        if existing:
            existing.summary = summary
            existing.explanation = explanation
            existing.remediation_steps = remediation_steps
            existing.validation_steps = validation_steps
            existing.cautions = cautions
            existing.generated_at = generated_at
            self.session.flush()
            return existing

        record = AIRecommendation(
            vulnerability_id=vulnerability_id,
            risk_assessment_id=risk_assessment_id,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            summary=summary,
            explanation=explanation,
            remediation_steps=remediation_steps,
            validation_steps=validation_steps,
            cautions=cautions,
            generated_at=generated_at,
        )
        self.session.add(record)
        self.session.flush()
        return record
