import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.api.responses.api_response import SuccessResponse
from app.core.enums import RiskLevel, RiskScope
from app.repositories.asset_repository import AssetRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.schemas.risk import RiskAssessmentListResponse, RiskAssessmentResponse
from app.services.risk_service import RiskService

router = APIRouter()


def get_risk_service(db: Session = Depends(get_db)) -> RiskService:
    """Dependency to inject a fully constructed RiskService into routes."""
    return RiskService(
        session=db,
        risk_repository=RiskRepository(db),
        scan_repository=ScanRepository(db),
        asset_repository=AssetRepository(db),
        scan_finding_repository=ScanFindingRepository(db),
    )


@router.get(
    "",
    response_model=SuccessResponse[RiskAssessmentListResponse],
    summary="Get all risk assessments",
)
def list_risk_assessments(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    scope: RiskScope | None = Query(None, description="Filter by risk scope"),
    risk_level: RiskLevel | None = Query(None, description="Filter by risk level"),
    service: RiskService = Depends(get_risk_service),
) -> dict:
    """Retrieve a paginated, filtered list of all persisted risk assessments."""
    items, total = service.get_risk_assessments(
        skip=skip, limit=limit, scope=scope, risk_level=risk_level
    )
    responses = [RiskAssessmentResponse.model_validate(item) for item in items]
    return {"data": RiskAssessmentListResponse(risk_assessments=responses, total=total)}


@router.get(
    "/assets/{asset_id}",
    response_model=SuccessResponse[RiskAssessmentListResponse],
    summary="Get risk history for an asset",
)
def get_risk_by_asset(
    asset_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    service: RiskService = Depends(get_risk_service),
) -> dict:
    """Retrieve the paginated asset-level risk history for a specific asset."""
    items, total = service.get_risk_by_asset(asset_id, skip=skip, limit=limit)
    responses = [RiskAssessmentResponse.model_validate(item) for item in items]
    return {"data": RiskAssessmentListResponse(risk_assessments=responses, total=total)}


@router.get(
    "/scans/{scan_id}",
    response_model=SuccessResponse[RiskAssessmentResponse],
    summary="Get risk for a scan",
)
def get_risk_by_scan(
    scan_id: uuid.UUID,
    service: RiskService = Depends(get_risk_service),
) -> dict:
    """Retrieve the calculated risk assessment for a specific scan."""
    risk = service.get_risk_by_scan(scan_id)
    return {"data": RiskAssessmentResponse.model_validate(risk)}


@router.post(
    "/scans/{scan_id}/calculate",
    response_model=SuccessResponse[RiskAssessmentResponse],
    summary="Calculate risk for a scan",
)
def calculate_risk_for_scan(
    scan_id: uuid.UUID,
    service: RiskService = Depends(get_risk_service),
) -> dict:
    """Trigger deterministic risk calculation for a scan's persisted findings.

    Safe to call repeatedly: recalculation updates existing risk records in
    place using the same deterministic rules.
    """
    risk = service.calculate_risk_for_scan(scan_id)
    return {"data": RiskAssessmentResponse.model_validate(risk)}


@router.get(
    "/summary",
    response_model=SuccessResponse[RiskAssessmentResponse],
    summary="Get overall assessment risk summary",
)
def get_summary(
    service: RiskService = Depends(get_risk_service),
) -> dict:
    """Retrieve the overall, system-wide assessment risk summary."""
    summary = service.get_summary()
    return {"data": RiskAssessmentResponse.model_validate(summary)}
