import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.audit import get_audit_context, get_audit_service
from app.api.dependencies.database import get_db
from app.api.responses.api_response import SuccessResponse
from app.audit.context import AuditContext
from app.repositories.scan_repository import ScanRepository
from app.repositories.target_repository import TargetRepository
from app.scanners.scanner_manager import ScannerManager
from app.schemas.scan import (
    CreateScanRequest,
    ScanListResponse,
    ScanResponse,
    ScanStatusResponse,
)
from app.services.audit_service import AuditService
from app.services.scan_service import ScanService

router = APIRouter()


def get_scan_service(
    db: Session = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
) -> ScanService:
    scan_repo = ScanRepository(db)
    target_repo = TargetRepository(db)
    return ScanService(
        scan_repository=scan_repo,
        target_repository=target_repo,
        audit_service=audit_service,
        scanner_engine=ScannerManager(),
    )


@router.post(
    "",
    response_model=SuccessResponse[ScanResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scan job",
)
def create_scan(
    request: CreateScanRequest,
    service: ScanService = Depends(get_scan_service),
    audit_context: AuditContext = Depends(get_audit_context),
) -> dict:
    """Create a new scan job for a validated target."""
    scan_job = service.create_scan(request, audit_context=audit_context)
    return {"data": ScanResponse.model_validate(scan_job)}


@router.get(
    "",
    response_model=SuccessResponse[ScanListResponse],
    summary="Get all scan jobs",
)
def list_scans(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    service: ScanService = Depends(get_scan_service),
) -> dict:
    """Retrieve a paginated list of all scan jobs."""
    scans = service.get_all_scans(skip=skip, limit=limit)
    total = service.count_scans()
    scan_responses = [ScanResponse.model_validate(s) for s in scans]
    return {"data": ScanListResponse(scans=scan_responses, total=total)}


@router.get(
    "/{scan_id}",
    response_model=SuccessResponse[ScanResponse],
    summary="Get a single scan job",
)
def get_scan(
    scan_id: uuid.UUID,
    service: ScanService = Depends(get_scan_service),
) -> dict:
    """Retrieve details of a specific scan job by its ID."""
    scan_job = service.get_scan(scan_id)
    return {"data": ScanResponse.model_validate(scan_job)}


@router.get(
    "/{scan_id}/status",
    response_model=SuccessResponse[ScanStatusResponse],
    summary="Get scan job status",
)
def get_scan_status(
    scan_id: uuid.UUID,
    service: ScanService = Depends(get_scan_service),
) -> dict:
    """Retrieve the current execution status of a scan job."""
    scan_job = service.get_scan(scan_id)
    status_response = ScanStatusResponse(
        scan_id=scan_job.id,
        status=scan_job.status,
        updated_at=scan_job.updated_at,
    )
    return {"data": status_response}


@router.delete(
    "/{scan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a scan job",
)
def delete_scan(
    scan_id: uuid.UUID,
    service: ScanService = Depends(get_scan_service),
    audit_context: AuditContext = Depends(get_audit_context),
) -> None:
    """Delete a scan job."""
    service.delete_scan(scan_id, audit_context=audit_context)
