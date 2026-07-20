import logging
import threading
import time
import uuid
from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.ai.manager import AIManager
from app.audit.context import AuditContext
from app.core.enums import (
    AuditEventCategory,
    AuditEventType,
    AuditOutcome,
    AuditResourceType,
    ScanProfile,
    ScanStatus,
)
from app.core.exceptions import (
    ConflictException,
    InternalException,
    NotFoundException,
    ParserException,
    ScannerCancelledException,
    ScannerExecutionException,
    ScannerTimeoutException,
)
from app.database.session import SessionLocal
from app.models.scan_job import ScanJob
from app.parsers.parser_manager import ParserManager
from app.repositories.asset_repository import AssetRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.network_service_repository import NetworkServiceRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.target_repository import TargetRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.scanners.interfaces import IScannerEngine
from app.scanners.scan_artifact import ScanArtifact
from app.scanners.scan_runtime import ScanRuntimeRegistry
from app.schemas.scan import CreateScanRequest
from app.services.ai_vulnerability_discovery_service import (
    AIVulnerabilityDiscoveryService,
)
from app.services.audit_service import AuditService
from app.services.inventory_service import InventoryService
from app.services.risk_service import RiskService

logger = logging.getLogger(__name__)


class ScanService:
    """Service layer for Scan Management business logic."""

    def __init__(
        self,
        scan_repository: ScanRepository,
        target_repository: TargetRepository,
        audit_service: AuditService,
        scanner_engine: IScannerEngine | None = None,
        session_factory: Callable[[], Session] | None = None,
        session_finalizer: Callable[[Session], None] | None = None,
        ai_manager: AIManager | None = None,
    ):
        self.scan_repository = scan_repository
        self.target_repository = target_repository
        self.scanner_engine = scanner_engine
        self.audit_service = audit_service
        # Passed through to AIVulnerabilityDiscoveryService for the post-scan
        # discovery step. None means "let it construct its own default
        # AIManager()" (the real provider) — tests inject a fake here so the
        # suite never makes a real network call to an AI provider.
        self.ai_manager = ai_manager
        # Opens the background execution thread's own DB session — the
        # request-scoped session passed above is closed by the time that
        # thread runs. Defaults to the real session factory; tests override
        # this to reuse their transactional test session instead.
        self.session_factory: Callable[[], Session] = session_factory or SessionLocal
        # Closes the background session once the scan finishes. Tests that
        # inject their own shared transactional session override this to a
        # no-op — closing it there would tear down the session the test
        # itself still needs afterward.
        self.session_finalizer: Callable[[Session], None] = session_finalizer or (
            lambda s: s.close()
        )
        # Exposes the most recently spawned background scan thread so tests
        # can deterministically wait for it (`.join()`) instead of racing
        # it. Not read by any production code path.
        self.last_scan_thread: threading.Thread | None = None

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
        """Create a new scan job and dispatch it to the scanner engine in
        the background.

        The HTTP request returns as soon as the job is persisted (status
        PENDING) — the actual scanner subprocess runs on a background
        thread with its own database session, since a scan can take
        minutes and must not block the request/response cycle. Callers
        should poll GET /scans/{id}/status (or /scans/{id}) for progress.
        """

        # Verify target exists
        target = self.target_repository.get_by_id(request.target_id)
        if not target:
            raise NotFoundException(f"Target with ID {request.target_id} not found.")

        # Check for duplicate active scans (business rule). PENDING is
        # included alongside RUNNING to close the race where a second scan
        # is requested before the background thread has flipped the first
        # scan's status to RUNNING.
        running_scans = self.scan_repository.get_running_scans_for_target(
            request.target_id
        )
        if running_scans:
            raise ConflictException(
                f"A scan is already running for target {request.target_id}."
            )

        # Every scan runs FULL regardless of what the request asks for: the
        # platform's discovery pipeline (asset/service inventory, AI
        # vulnerability inference, risk scoring) depends on complete port
        # and service data, which only the FULL profile reliably produces.
        # request.scan_profile is intentionally never trusted here.
        scan_profile = ScanProfile.FULL.value

        # Create scan job
        scan_job = ScanJob(
            target_id=target.id,
            scan_type=scan_profile,
            status=ScanStatus.PENDING,
        )
        scan_job = self.scan_repository.create(scan_job)

        self._commit_with_audit(
            event_type=AuditEventType.SCAN_CREATED,
            resource_id=scan_job.id,
            context=audit_context or AuditContext.system(),
            metadata={"scan_type": scan_job.scan_type, "status": scan_job.status.value},
        )

        if self.scanner_engine:
            thread = threading.Thread(
                target=self._run_scan_in_background,
                args=(scan_job.id, target.target, scan_profile),
                name=f"scan-{scan_job.id}",
                daemon=True,
            )
            self.last_scan_thread = thread
            thread.start()

        return scan_job

    def _run_scan_in_background(
        self, scan_id: uuid.UUID, target: str, scan_profile: str
    ) -> None:
        """Execute the scanner engine off the request thread and persist the outcome.

        Runs on its own DB session (the request-scoped session passed into
        this service is closed by the time the HTTP response is sent).
        Never raises — all failure paths are logged and reflected in the
        scan job's status instead, since there is no caller left to
        propagate an exception to.
        """
        session = self.session_factory()
        try:
            scan_repo = ScanRepository(session)
            audit_service = AuditService(AuditRepository(session))

            scan_job = scan_repo.get_by_id(scan_id)
            if scan_job is None:
                logger.error(
                    "Scan job vanished before background execution could start",
                    extra={"scan_id": str(scan_id)},
                )
                return

            scan_job.status = ScanStatus.RUNNING
            scan_job.started_at = datetime.now(UTC)
            scan_repo.update(scan_job)
            session.commit()
            monotonic_start = time.monotonic()

            try:
                if self.scanner_engine is None:
                    # create_scan only starts this background thread inside
                    # `if self.scanner_engine:`, so this is unreachable in
                    # practice — narrows the type for mypy across the thread
                    # boundary, and still routes through the same
                    # failure-handling path below rather than raising
                    # uncaught out of this method (see its docstring).
                    raise InternalException(
                        "Background scan execution started without a scanner engine."
                    )
                artifact = self.scanner_engine.dispatch_scan(
                    scan_id=scan_id, target=target, scan_profile=scan_profile
                )
            except ScannerCancelledException as exc:
                final_status = ScanStatus.CANCELLED
                failure_reason = "Scan was cancelled by user request."
                event_type = AuditEventType.SCAN_CANCELLED
                outcome = AuditOutcome.SUCCESS
                stdout = exc.details.get("stdout", "")
                stderr = exc.details.get("stderr", "")
                output_path = exc.details.get("output_path")
            except (ScannerTimeoutException, ScannerExecutionException) as exc:
                final_status = ScanStatus.FAILED
                failure_reason = exc.message
                event_type = AuditEventType.SCAN_FAILED
                outcome = AuditOutcome.FAILURE
                stdout = exc.details.get("stdout", "")
                stderr = exc.details.get("stderr", "")
                output_path = exc.details.get("output_path")
            except Exception as exc:  # noqa: BLE001 - last-resort, must not crash the thread
                final_status = ScanStatus.FAILED
                failure_reason = str(exc)
                event_type = AuditEventType.SCAN_FAILED
                outcome = AuditOutcome.FAILURE
                stdout, stderr, output_path = "", "", None
                logger.exception(
                    "Unhandled error during background scan execution",
                    extra={"scan_id": str(scan_id)},
                )
            else:
                # Dispatch succeeded: hand off to the parser/inventory/AI/risk
                # chain, which owns status + commit for this outcome — the
                # shared finalize block below is for CANCELLED/TIMEOUT/ERROR
                # paths only and must not run for a successful dispatch.
                self._process_successful_scan(
                    session,
                    scan_repo,
                    audit_service,
                    scan_id,
                    artifact,
                    monotonic_start,
                )
                return

            scan_job.status = final_status
            scan_job.completed_at = datetime.now(UTC)
            # Measured directly rather than by subtracting started_at from
            # completed_at: started_at round-trips through the DB (the
            # commit above expires it) and may come back timezone-naive
            # depending on the backend, while completed_at is always
            # timezone-aware — subtracting the two can raise TypeError.
            scan_job.execution_duration = time.monotonic() - monotonic_start
            scan_job.failure_reason = failure_reason
            scan_job.output_file_path = str(output_path) if output_path else None
            scan_job.stdout_log = stdout
            scan_job.stderr_log = stderr
            scan_repo.update(scan_job)

            try:
                audit_service.append_event(
                    event_type=event_type,
                    category=AuditEventCategory.SCAN,
                    outcome=outcome,
                    context=AuditContext.system(),
                    resource_type=AuditResourceType.SCAN,
                    resource_id=scan_id,
                    scan_id=scan_id,
                    metadata={"status": final_status.value},
                )
                session.commit()
            except Exception:
                session.rollback()
                logger.error(
                    "Failed to commit scan completion audit event; scan job status "
                    "update was rolled back with it",
                    extra={"scan_id": str(scan_id)},
                    exc_info=True,
                )
        finally:
            self.session_finalizer(session)

    def _process_successful_scan(
        self,
        session: Session,
        scan_repo: ScanRepository,
        audit_service: AuditService,
        scan_id: uuid.UUID,
        artifact: ScanArtifact,
        monotonic_start: float,
    ) -> None:
        """Parse a successful scan's raw output into inventory, then
        best-effort run AI vulnerability discovery and risk scoring.

        InventoryService.process_assessment_package owns scan_job.status and
        commit for this outcome (COMPLETED on success, FAILED on its own
        internal failure) — this method only sets scan_job.status directly
        for a ParserException, where inventory never got a chance to run.
        """
        try:
            package = ParserManager().parse_artifact(artifact)
        except ParserException as exc:
            scan_job = scan_repo.get_by_id(scan_id)
            if scan_job is None:
                return
            scan_job.status = ScanStatus.FAILED
            scan_job.completed_at = datetime.now(UTC)
            scan_job.execution_duration = time.monotonic() - monotonic_start
            scan_job.failure_reason = str(exc)
            scan_job.output_file_path = (
                str(artifact.output_path) if artifact.output_path else None
            )
            scan_job.stdout_log = artifact.stdout
            scan_job.stderr_log = artifact.stderr
            scan_repo.update(scan_job)
            try:
                audit_service.append_event(
                    event_type=AuditEventType.SCAN_FAILED,
                    category=AuditEventCategory.SCAN,
                    outcome=AuditOutcome.FAILURE,
                    context=AuditContext.system(),
                    resource_type=AuditResourceType.SCAN,
                    resource_id=scan_id,
                    scan_id=scan_id,
                    metadata={
                        "status": ScanStatus.FAILED.value,
                        "failure_category": "ParserException",
                    },
                )
                session.commit()
            except Exception:
                session.rollback()
                logger.error(
                    "Failed to commit parser-failure audit event for scan",
                    extra={"scan_id": str(scan_id)},
                    exc_info=True,
                )
            return

        inventory_service = InventoryService(
            session,
            AssetRepository(session),
            VulnerabilityRepository(session),
            scan_repo,
            audit_service,
        )
        try:
            inventory_service.process_assessment_package(package, AuditContext.system())
        except Exception:
            logger.exception(
                "Inventory processing failed for scan; scan_job status was "
                "already handled internally by InventoryService",
                extra={"scan_id": str(scan_id)},
            )
            return

        scan_job = scan_repo.get_by_id(scan_id)
        if scan_job is None or scan_job.status != ScanStatus.COMPLETED:
            return

        # Raw scanner output fields aren't known to InventoryService — attach
        # them onto the now-COMPLETED scan job separately.
        scan_job.output_file_path = (
            str(artifact.output_path) if artifact.output_path else None
        )
        scan_job.stdout_log = artifact.stdout
        scan_job.stderr_log = artifact.stderr
        scan_job.execution_duration = time.monotonic() - monotonic_start
        scan_repo.update(scan_job)
        session.commit()

        # Best-effort from here on: a failure in AI discovery or risk
        # calculation must never undo the COMPLETED scan or the asset/service
        # inventory already committed above.
        try:
            ai_discovery_service = AIVulnerabilityDiscoveryService(
                session,
                inventory_service,
                AssetRepository(session),
                NetworkServiceRepository(session),
                audit_service,
                ai_manager=self.ai_manager,
            )
            ai_discovery_service.discover_for_package(package, AuditContext.system())
        except Exception:
            logger.exception(
                "AI vulnerability discovery failed for scan; scan results are "
                "otherwise unaffected",
                extra={"scan_id": str(scan_id)},
            )

        try:
            risk_service = RiskService(
                session,
                RiskRepository(session),
                scan_repo,
                AssetRepository(session),
                ScanFindingRepository(session),
                audit_service,
            )
            risk_service.calculate_risk_for_scan(scan_id, AuditContext.system())
        except Exception:
            logger.exception(
                "Automatic risk calculation failed for scan",
                extra={"scan_id": str(scan_id)},
            )

    def cancel_scan(
        self, scan_id: uuid.UUID, audit_context: AuditContext | None = None
    ) -> ScanJob:
        """Request cancellation of a running scan job.

        This only flags the executing subprocess to stop; the scan job's
        status transitions to CANCELLED asynchronously once the background
        thread notices (within about a second) and persists whatever
        output the scanner had produced so far.
        """
        scan_job = self.get_scan(scan_id)
        if scan_job.status != ScanStatus.RUNNING:
            raise ConflictException(
                f"Scan {scan_id} is not running (current status: "
                f"{scan_job.status.value}); only running scans can be cancelled."
            )

        if not ScanRuntimeRegistry.request_cancel(scan_id):
            raise ConflictException(
                f"No active scanner process found for scan {scan_id}; it may have "
                "just finished, or the server was restarted after it started."
            )

        return scan_job

    def get_scan(self, scan_id: uuid.UUID) -> ScanJob:
        """Retrieve a scan job by its ID."""
        scan_job = self.scan_repository.get_by_id(scan_id)
        if not scan_job:
            raise NotFoundException(f"Scan job with ID {scan_id} not found.")
        return scan_job

    def get_all_scans(
        self, skip: int = 0, limit: int = 100, target_id: uuid.UUID | None = None
    ) -> Sequence[ScanJob]:
        """Retrieve all scan jobs, optionally scoped to one target."""
        return self.scan_repository.get_all(skip=skip, limit=limit, target_id=target_id)

    def count_scans(self, target_id: uuid.UUID | None = None) -> int:
        """Count scan jobs, optionally scoped to one target."""
        return self.scan_repository.count(target_id=target_id)

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
