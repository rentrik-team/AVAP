from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.api.responses.api_response import SuccessResponse
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.risk_repository import RiskRepository
from app.schemas.dashboard import (
    DashboardAIStatisticsResponse,
    DashboardAssetStatisticsResponse,
    DashboardReportStatisticsResponse,
    DashboardRiskStatisticsResponse,
    DashboardScanStatisticsResponse,
    DashboardSummaryResponse,
    DashboardVulnerabilityStatisticsResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter()


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    """Dependency to inject a fully constructed, read-only DashboardService."""
    return DashboardService(
        dashboard_repository=DashboardRepository(db),
        risk_repository=RiskRepository(db),
        report_repository=ReportRepository(db),
    )


@router.get(
    "/summary",
    response_model=SuccessResponse[DashboardSummaryResponse],
    summary="Get executive platform summary",
)
def get_summary(
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """Retrieve overall platform statistics for the executive dashboard."""
    return {"data": service.get_summary()}


@router.get(
    "/assets",
    response_model=SuccessResponse[DashboardAssetStatisticsResponse],
    summary="Get asset inventory statistics",
)
def get_asset_statistics(
    limit: int = Query(10, ge=1, le=50, description="Max recently discovered assets"),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """Retrieve asset inventory and service exposure statistics."""
    return {"data": service.get_asset_statistics(limit=limit)}


@router.get(
    "/vulnerabilities",
    response_model=SuccessResponse[DashboardVulnerabilityStatisticsResponse],
    summary="Get vulnerability catalog statistics",
)
def get_vulnerability_statistics(
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """Retrieve vulnerability catalog and severity distribution statistics."""
    return {"data": service.get_vulnerability_statistics()}


@router.get(
    "/risk",
    response_model=SuccessResponse[DashboardRiskStatisticsResponse],
    summary="Get deterministic risk posture statistics",
)
def get_risk_statistics(
    top_limit: int = Query(
        10, ge=1, le=50, description="Max top-risk assets/vulnerabilities to return"
    ),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """Retrieve deterministic risk posture, sourced only from Module 06 data."""
    return {"data": service.get_risk_statistics(top_limit=top_limit)}


@router.get(
    "/scans",
    response_model=SuccessResponse[DashboardScanStatisticsResponse],
    summary="Get scan execution statistics",
)
def get_scan_statistics(
    limit: int = Query(10, ge=1, le=50, description="Max recent scans to return"),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """Retrieve scan execution and operational statistics."""
    return {"data": service.get_scan_statistics(limit=limit)}


@router.get(
    "/reports",
    response_model=SuccessResponse[DashboardReportStatisticsResponse],
    summary="Get report generation statistics",
)
def get_report_statistics(
    limit: int = Query(10, ge=1, le=50, description="Max recent reports to return"),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """Retrieve report generation statistics from Module 08 metadata."""
    return {"data": service.get_report_statistics(limit=limit)}


@router.get(
    "/ai",
    response_model=SuccessResponse[DashboardAIStatisticsResponse],
    summary="Get AI remediation recommendation statistics",
)
def get_ai_statistics(
    service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """Retrieve AI recommendation availability and freshness-based coverage."""
    return {"data": service.get_ai_statistics()}
