import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.manager import AIManager
from app.api.dependencies.audit import get_audit_context, get_audit_service
from app.api.dependencies.database import get_db
from app.api.responses.api_response import SuccessResponse
from app.audit.context import AuditContext
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.network_service_repository import NetworkServiceRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.schemas.ai import (
    AIModelResponse,
    AIProviderListResponse,
    AIRecommendationResponse,
)
from app.services.ai_service import AIService
from app.services.audit_service import AuditService

router = APIRouter()


def get_ai_service(
    db: Session = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
) -> AIService:
    """Dependency to inject a fully constructed AIService into routes."""
    return AIService(
        session=db,
        ai_recommendation_repository=AIRecommendationRepository(db),
        risk_repository=RiskRepository(db),
        vulnerability_repository=VulnerabilityRepository(db),
        network_service_repository=NetworkServiceRepository(db),
        audit_service=audit_service,
    )


@router.get(
    "/recommendations/{assessment_id}",
    response_model=SuccessResponse[AIRecommendationResponse],
    summary="Get the AI recommendation for a risk assessment",
)
def get_recommendation(
    assessment_id: uuid.UUID,
    service: AIService = Depends(get_ai_service),
) -> dict:
    """Retrieve the persisted AI remediation recommendation for a
    vulnerability-scoped risk assessment, without triggering generation."""
    recommendation = service.get_recommendation(assessment_id)
    return {"data": AIRecommendationResponse.model_validate(recommendation)}


@router.post(
    "/recommendations/{assessment_id}/generate",
    response_model=SuccessResponse[AIRecommendationResponse],
    summary="Generate the AI recommendation for a risk assessment",
)
def generate_recommendation(
    assessment_id: uuid.UUID,
    service: AIService = Depends(get_ai_service),
    audit_context: AuditContext = Depends(get_audit_context),
) -> dict:
    """Generate an AI remediation recommendation for a vulnerability-scoped
    risk assessment. Safe to call repeatedly: an existing recommendation is
    reused as long as the risk assessment has not been recalculated since.
    """
    recommendation = service.generate_recommendation(
        assessment_id, audit_context=audit_context
    )
    return {"data": AIRecommendationResponse.model_validate(recommendation)}


@router.get(
    "/providers",
    response_model=SuccessResponse[AIProviderListResponse],
    summary="List supported and active AI providers",
)
def list_providers() -> dict:
    """Retrieve the supported AI providers and the currently configured one."""
    manager = AIManager()
    data = AIProviderListResponse(
        supported_providers=manager.supported_providers(),
        active_provider=manager.resolve_provider_name(),
    )
    return {"data": data}


@router.get(
    "/models",
    response_model=SuccessResponse[AIModelResponse],
    summary="Get the currently configured AI model",
)
def get_model_info() -> dict:
    """Retrieve the model configured for the active AI provider."""
    manager = AIManager()
    data = AIModelResponse(
        provider=manager.resolve_provider_name(),
        model=manager.resolve_model_name(),
    )
    return {"data": data}
