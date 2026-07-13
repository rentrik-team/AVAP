import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.audit import get_audit_context, get_audit_service
from app.api.dependencies.database import get_db
from app.audit.context import AuditContext
from app.repositories.scan_repository import ScanRepository
from app.repositories.target_repository import TargetRepository
from app.schemas.scan import (
    CreateScanRequest,
    ScanListResponse,
    ScanResponse,
    ScanStatusResponse,
)
from app.services.audit_service import AuditService
from app.services.scan_service import ScanService

from app.scanners.scanner_manager import ScannerManager

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
        scanner_engine=ScannerManager()
    )


@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
def create_scan(
    request: CreateScanRequest,
    service: ScanService = Depends(get_scan_service),
    audit_context: AuditContext = Depends(get_audit_context),
) -> Any:
    """
    Create a new scan job for a validated target.
    """
    return service.create_scan(request, audit_context=audit_context)


@router.get("/", response_model=ScanListResponse)
def list_scans(
    skip: int = 0,
    limit: int = 100,
    service: ScanService = Depends(get_scan_service),
) -> Any:
    """
    Retrieve a paginated list of all scan jobs.
    """
    scans = service.get_all_scans(skip=skip, limit=limit)
    total = service.count_scans()
    return {"scans": scans, "total": total}


@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan(
    scan_id: uuid.UUID,
    service: ScanService = Depends(get_scan_service),
) -> Any:
    """
    Retrieve details of a specific scan job by its ID.
    """
    return service.get_scan(scan_id)


@router.get("/{scan_id}/status", response_model=ScanStatusResponse)
def get_scan_status(
    scan_id: uuid.UUID,
    service: ScanService = Depends(get_scan_service),
) -> Any:
    """
    Retrieve the current execution status of a scan job.
    """
    scan = service.get_scan(scan_id)
    return {
        "scan_id": scan.id,
        "status": scan.status,
        "updated_at": scan.updated_at,
    }


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan(
    scan_id: uuid.UUID,
    service: ScanService = Depends(get_scan_service),
    audit_context: AuditContext = Depends(get_audit_context),
) -> None:
    """
    Delete a scan job.
    """
    service.delete_scan(scan_id, audit_context=audit_context)
