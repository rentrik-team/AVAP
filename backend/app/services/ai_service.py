import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.ai.manager import AIManager
from app.ai.prompt_builder import PROMPT_VERSION, build_prompt
from app.ai.response_validator import validate_response
from app.core.enums import RiskScope
from app.core.exceptions import InsufficientContextException, NotFoundException
from app.models.ai_recommendation import AIRecommendation
from app.models.risk_assessment import RiskAssessment
from app.models.service import NetworkService
from app.models.vulnerability import Vulnerability
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.network_service_repository import NetworkServiceRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.schemas.ai import AIRemediationContext

logger = logging.getLogger(__name__)


def _build_remediation_context(
    vulnerability: Vulnerability,
    risk_assessment: RiskAssessment,
    service: NetworkService | None,
) -> AIRemediationContext:
    """Assemble the provider-neutral AI context from persisted Module 05/06 data.

    Constructed field-by-field; SQLAlchemy models are never serialized directly.
    """
    return AIRemediationContext(
        vulnerability_id=vulnerability.id,
        vulnerability_name=vulnerability.name,
        cve=vulnerability.cve,
        description=vulnerability.description,
        severity_rating=vulnerability.severity_rating,
        severity_score=vulnerability.severity_score,
        risk_score=risk_assessment.risk_score,
        risk_level=risk_assessment.risk_level,
        calculation_version=risk_assessment.calculation_version,
        affected_service_name=service.service_name if service else None,
        affected_product=service.product if service else None,
        affected_version=service.version if service else None,
    )


class AIService:
    """Service layer for AI-assisted remediation business orchestration.

    Owns the transaction boundary for recommendation persistence and
    coordinates the deterministic Risk/Vulnerability context with the
    provider-neutral AI Engine. Contains zero provider-specific logic.
    """

    def __init__(
        self,
        session: Session,
        ai_recommendation_repository: AIRecommendationRepository,
        risk_repository: RiskRepository,
        vulnerability_repository: VulnerabilityRepository,
        network_service_repository: NetworkServiceRepository,
        ai_manager: AIManager | None = None,
    ):
        self.session = session
        self.ai_recommendation_repository = ai_recommendation_repository
        self.risk_repository = risk_repository
        self.vulnerability_repository = vulnerability_repository
        self.network_service_repository = network_service_repository
        self.ai_manager = ai_manager or AIManager()

    def _get_vulnerability_risk_assessment(
        self, risk_assessment_id: uuid.UUID
    ) -> RiskAssessment:
        """Fetch and validate the risk assessment required for generation."""
        risk_assessment = self.risk_repository.get_by_id(risk_assessment_id)
        if not risk_assessment:
            raise NotFoundException(f"Risk assessment {risk_assessment_id} not found.")

        if risk_assessment.scope != RiskScope.VULNERABILITY:
            raise InsufficientContextException(
                "AI recommendations require a VULNERABILITY-scoped risk assessment."
            )
        return risk_assessment

    def generate_recommendation(
        self, risk_assessment_id: uuid.UUID
    ) -> AIRecommendation:
        """Generate (or return the still-valid) remediation recommendation.

        If a recommendation already exists for the current provider, model,
        and prompt version, and the risk assessment has not been recalculated
        since it was generated, the existing recommendation is returned
        without calling the AI provider again. Otherwise a fresh recommendation
        is generated and persisted, updating any prior record for the same
        identity in place.
        """
        risk_assessment = self._get_vulnerability_risk_assessment(risk_assessment_id)

        vulnerability = self.vulnerability_repository.get_by_id(
            risk_assessment.vulnerability_id
        )
        if not vulnerability:
            raise NotFoundException(
                f"Vulnerability {risk_assessment.vulnerability_id} not found."
            )

        provider_name = self.ai_manager.resolve_provider_name()
        model_name = self.ai_manager.resolve_model_name()

        existing = self.ai_recommendation_repository.find_identity_record(
            risk_assessment_id=risk_assessment.id,
            provider=provider_name,
            model=model_name,
            prompt_version=PROMPT_VERSION,
        )
        if existing and existing.generated_at >= risk_assessment.calculated_at:
            return existing

        service = None
        if risk_assessment.service_id:
            service = self.network_service_repository.get_by_id(
                risk_assessment.service_id
            )

        context = _build_remediation_context(vulnerability, risk_assessment, service)
        prompt = build_prompt(context)

        logger.info(
            "AI recommendation generation started",
            extra={
                "vulnerability_id": str(vulnerability.id),
                "risk_assessment_id": str(risk_assessment.id),
                "provider": provider_name,
                "model": model_name,
            },
        )

        provider_response = self.ai_manager.generate(prompt)
        recommendation_output = validate_response(provider_response.content)

        try:
            record = self.ai_recommendation_repository.upsert(
                vulnerability_id=vulnerability.id,
                risk_assessment_id=risk_assessment.id,
                provider=provider_response.provider,
                model=provider_response.model,
                prompt_version=PROMPT_VERSION,
                summary=recommendation_output.summary,
                explanation=recommendation_output.explanation,
                remediation_steps=recommendation_output.remediation_steps,
                validation_steps=recommendation_output.validation_steps,
                cautions=recommendation_output.cautions,
                generated_at=datetime.now(UTC),
            )
            self.session.commit()
        except Exception:
            logger.error(
                "Failed to persist AI recommendation, rolling back transaction",
                extra={
                    "vulnerability_id": str(vulnerability.id),
                    "risk_assessment_id": str(risk_assessment.id),
                },
                exc_info=True,
            )
            self.session.rollback()
            raise

        logger.info(
            "AI recommendation generation completed",
            extra={
                "vulnerability_id": str(vulnerability.id),
                "risk_assessment_id": str(risk_assessment.id),
                "provider": provider_name,
                "model": model_name,
            },
        )
        self.session.refresh(record)
        return record

    def get_recommendation(self, risk_assessment_id: uuid.UUID) -> AIRecommendation:
        """Retrieve the persisted recommendation for a risk assessment."""
        recommendation = self.ai_recommendation_repository.get_by_risk_assessment(
            risk_assessment_id
        )
        if not recommendation:
            raise NotFoundException(
                f"No AI recommendation exists for risk assessment {risk_assessment_id}."
            )
        return recommendation
