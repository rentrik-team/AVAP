import logging
import uuid
from collections.abc import Sequence

from app.audit.context import AuditContext
from app.core.enums import (
    AuditEventCategory,
    AuditEventType,
    AuditOutcome,
    AuditResourceType,
    ScanStatus,
)
from app.core.exceptions import ConflictException, NotFoundException
from app.models.scan_job import ScanJob
from app.repositories.scan_repository import ScanRepository
from app.repositories.target_repository import TargetRepository
from app.scanners.interfaces import IScannerEngine
from app.schemas.scan import CreateScanRequest
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class ScanService:
    """Service layer for Scan Management business logic."""

    def __init__(
        self,
        scan_repository: ScanRepository,
        target_repository: TargetRepository,
        audit_service: AuditService,
        scanner_engine: IScannerEngine | None = None,
    ):
        self.scan_repository = scan_repository
        self.target_repository = target_repository
        self.scanner_engine = scanner_engine
        self.audit_service = audit_service

    def _commit_with_audit(
        self,
        event_type: AuditEventType,
        resource_id: uuid.UUID,
        context: AuditContext,
        metadata: dict | None = None,
    ) -> None:
        """Append a SCAN-category audit event in the same transaction as the
        already-flushed scan mutation, then commit both atomically.

        Shared transaction (preferred pattern, see backend.md → "Audit
        event transaction pattern"): if the audit insert or its metadata
        validation fails, this raises before commit and the entire
        mutation (repository flush included) rolls back rather than being
        reported as successful.
        """
        try:
            self.audit_service.append_event(
                event_type=event_type,
                category=AuditEventCategory.SCAN,
                outcome=AuditOutcome.SUCCESS,
                context=context,
                resource_type=AuditResourceType.SCAN,
                resource_id=resource_id,
                scan_id=resource_id,
                metadata=metadata,
            )
            self.scan_repository.session.commit()
        except Exception:
            self.scan_repository.session.rollback()
            logger.error(
                "Scan mutation failed to commit; transaction rolled back.",
                extra={"event_type": event_type.value, "resource_id": str(resource_id)},
                exc_info=True,
            )
            raise

    def create_scan(
        self, request: CreateScanRequest, audit_context: AuditContext | None = None
    ) -> ScanJob:
        """Create a new scan job and optionally dispatch it to the scanner engine."""

        # Verify target exists
        target = self.target_repository.get_by_id(request.target_id)
        if not target:
            raise NotFoundException(f"Target with ID {request.target_id} not found.")

        # Check for duplicate running scans (business rule)
        running_scans = self.scan_repository.get_running_scans_for_target(
            request.target_id
        )
        if running_scans:
            raise ConflictException(
                f"A scan is already running for target {request.target_id}."
            )

        # Create scan job
        scan_job = ScanJob(
            target_id=target.id,
            scan_type=request.scan_profile,
            status=ScanStatus.PENDING,
        )
        scan_job = self.scan_repository.create(scan_job)

        # Dispatch to scanner engine if available
        if self.scanner_engine:
            # We assume the dispatch_scan is async or handles backgrounding
            self.scanner_engine.dispatch_scan(
                scan_id=scan_job.id,
                target=target.target,
                scan_profile=request.scan_profile,
            )
            scan_job.status = ScanStatus.RUNNING
            self.scan_repository.update(scan_job)

        self._commit_with_audit(
            event_type=AuditEventType.SCAN_CREATED,
            resource_id=scan_job.id,
            context=audit_context or AuditContext.system(),
            metadata={"scan_type": scan_job.scan_type, "status": scan_job.status.value},
        )
        return scan_job

    def get_scan(self, scan_id: uuid.UUID) -> ScanJob:
        """Retrieve a scan job by its ID."""
        scan_job = self.scan_repository.get_by_id(scan_id)
        if not scan_job:
            raise NotFoundException(f"Scan job with ID {scan_id} not found.")
        return scan_job

    def get_all_scans(self, skip: int = 0, limit: int = 100) -> Sequence[ScanJob]:
        """Retrieve all scan jobs."""
        return self.scan_repository.get_all(skip=skip, limit=limit)

    def count_scans(self) -> int:
        """Count total scan jobs."""
        return self.scan_repository.count()

    def delete_scan(
        self, scan_id: uuid.UUID, audit_context: AuditContext | None = None
    ) -> None:
        """Delete a scan job."""
        scan_job = self.get_scan(scan_id)
        # Note: Depending on business rules, we might not want to delete running scans
        if scan_job.status == ScanStatus.RUNNING:
            raise ConflictException("Cannot delete a running scan.")

        scan_type = scan_job.scan_type
        self.scan_repository.delete(scan_job)

        self._commit_with_audit(
            event_type=AuditEventType.SCAN_DELETED,
            resource_id=scan_id,
            context=audit_context or AuditContext.system(),
            metadata={"scan_type": scan_type},
        )
