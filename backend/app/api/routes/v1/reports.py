import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.api.responses.api_response import SuccessResponse
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.network_service_repository import NetworkServiceRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.schemas.report import (
    GenerateReportRequest,
    ReportListResponse,
    ReportResponse,
)
from app.services.report_service import ReportService

router = APIRouter()


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """Dependency to inject a fully constructed ReportService into routes."""
    return ReportService(
        session=db,
        report_repository=ReportRepository(db),
        scan_repository=ScanRepository(db),
        risk_repository=RiskRepository(db),
        asset_repository=AssetRepository(db),
        vulnerability_repository=VulnerabilityRepository(db),
        network_service_repository=NetworkServiceRepository(db),
        scan_finding_repository=ScanFindingRepository(db),
        ai_recommendation_repository=AIRecommendationRepository(db),
    )


@router.post(
    "",
    response_model=SuccessResponse[ReportResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new report",
)
def generate_report(
    request: GenerateReportRequest,
    service: ReportService = Depends(get_report_service),
) -> dict:
    """Generate a new immutable PDF report for a scan's current assessment state."""
    report = service.generate_report(request.scan_id)
    return {"data": ReportResponse.model_validate(report)}


@router.get(
    "",
    response_model=SuccessResponse[ReportListResponse],
    summary="List generated reports",
)
def list_reports(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    scan_id: uuid.UUID | None = Query(None, description="Filter by source scan"),
    service: ReportService = Depends(get_report_service),
) -> dict:
    """Retrieve a paginated, optionally scan-filtered list of report metadata."""
    items, total = service.get_reports(skip=skip, limit=limit, scan_id=scan_id)
    responses = [ReportResponse.model_validate(item) for item in items]
    return {"data": ReportListResponse(reports=responses, total=total)}


@router.get(
    "/{report_id}",
    response_model=SuccessResponse[ReportResponse],
    summary="Get report metadata",
)
def get_report(
    report_id: uuid.UUID,
    service: ReportService = Depends(get_report_service),
) -> dict:
    """Retrieve metadata for a specific generated report."""
    report = service.get_report(report_id)
    return {"data": ReportResponse.model_validate(report)}


@router.get(
    "/{report_id}/download",
    summary="Download the generated report file",
)
def download_report(
    report_id: uuid.UUID,
    service: ReportService = Depends(get_report_service),
) -> FileResponse:
    """Download the generated PDF report.

    The file path is resolved entirely server-side from the report's
    server-generated file name and the configured storage root; no
    client-supplied path or filename is ever used.
    """
    file_path = service.get_report_file_path(report_id)
    download_name = f"avap-report-{report_id}.pdf"
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=download_name,
    )


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a report",
)
def delete_report(
    report_id: uuid.UUID,
    service: ReportService = Depends(get_report_service),
) -> None:
    """Delete a report's metadata and its associated stored file."""
    service.delete_report(report_id)
