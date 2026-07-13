import logging
import os
import tempfile
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.audit.context import AuditContext
from app.core.config import Settings, get_settings
from app.core.enums import AuditEventCategory, AuditEventType, AuditOutcome, AuditResourceType
from app.core.exceptions import (
    InsufficientReportDataException,
    NotFoundException,
    ReportRenderingException,
    ReportStorageException,
)
from app.models.report import Report
from app.reporting.generator import REPORT_TEMPLATE_VERSION, build_report_data
from app.reporting.pdf import render_pdf
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.network_service_repository import NetworkServiceRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

_PDF_SIGNATURE = b"%PDF-"


class ReportService:
    """Service layer for Reporting Engine business orchestration.

    Owns the transaction boundary for report metadata persistence and the
    atomic publication of the generated PDF file. Contains no ReportLab
    layout logic and performs no risk calculation or AI generation itself.
    """

    def __init__(
        self,
        session: Session,
        report_repository: ReportRepository,
        scan_repository: ScanRepository,
        risk_repository: RiskRepository,
        asset_repository: AssetRepository,
        vulnerability_repository: VulnerabilityRepository,
        network_service_repository: NetworkServiceRepository,
        scan_finding_repository: ScanFindingRepository,
        ai_recommendation_repository: AIRecommendationRepository,
        audit_service: AuditService,
        settings: Settings | None = None,
    ):
        self.session = session
        self.report_repository = report_repository
        self.scan_repository = scan_repository
        self.risk_repository = risk_repository
        self.asset_repository = asset_repository
        self.vulnerability_repository = vulnerability_repository
        self.network_service_repository = network_service_repository
        self.scan_finding_repository = scan_finding_repository
        self.ai_recommendation_repository = ai_recommendation_repository
        self.audit_service = audit_service
        self.settings = settings or get_settings()

    def _storage_root(self) -> Path:
        root = self.settings.report_output_path
        root.mkdir(parents=True, exist_ok=True)
        return root

    def generate_report(
        self, scan_id: uuid.UUID, audit_context: AuditContext | None = None
    ) -> Report:
        """Generate a new immutable report for a scan's current assessment state.

        Every call renders and persists a brand new report; existing reports
        for the same scan are never overwritten or deleted, preserving full
        report history.
        """
        context = audit_context or AuditContext.system()
        scan_job = self.scan_repository.get_by_id(scan_id)
        if not scan_job:
            raise NotFoundException(f"Scan job with ID {scan_id} not found.")

        scan_risk = self.risk_repository.get_by_scan(scan_id)
        if not scan_risk:
            raise InsufficientReportDataException(
                f"No deterministic risk assessment is available for scan {scan_id}."
            )

        generated_at = datetime.now(UTC)
        report_data = build_report_data(
            scan_job=scan_job,
            scan_risk=scan_risk,
            generated_at=generated_at,
            risk_repository=self.risk_repository,
            asset_repository=self.asset_repository,
            vulnerability_repository=self.vulnerability_repository,
            network_service_repository=self.network_service_repository,
            scan_finding_repository=self.scan_finding_repository,
            ai_recommendation_repository=self.ai_recommendation_repository,
        )

        logger.info(
            "Report generation started",
            extra={
                "scan_id": str(scan_id),
                "vulnerability_count": len(report_data.findings),
            },
        )

        report_id = uuid.uuid4()
        file_name = f"report_{report_id}.pdf"
        final_path = self._storage_root() / file_name

        final_path_published = False
        try:
            tmp_fd, tmp_name = tempfile.mkstemp(
                suffix=".pdf.tmp", dir=self._storage_root()
            )
            os.close(tmp_fd)
            tmp_path = Path(tmp_name)
            try:
                render_pdf(report_data, tmp_path)
                self._validate_pdf(tmp_path)
                file_size = tmp_path.stat().st_size
                os.replace(tmp_path, final_path)
                final_path_published = True
            except Exception as exc:
                tmp_path.unlink(missing_ok=True)
                logger.error(
                    "Report rendering failed",
                    extra={"scan_id": str(scan_id)},
                    exc_info=True,
                )
                raise ReportRenderingException(
                    "Failed to render the report PDF."
                ) from exc

            ai_recommendations_included = sum(
                1 for finding in report_data.findings if finding.remediation is not None
            )

            report = Report(
                id=report_id,
                scan_id=scan_id,
                format="PDF",
                report_template_version=REPORT_TEMPLATE_VERSION,
                risk_calculation_version=scan_risk.calculation_version,
                source_risk_calculated_at=scan_risk.calculated_at,
                overall_risk_score=report_data.executive_summary.overall_risk_score,
                overall_risk_level=report_data.executive_summary.overall_risk_level,
                vulnerability_count=len(report_data.findings),
                ai_recommendations_included=ai_recommendations_included,
                file_name=file_name,
                file_size_bytes=file_size,
                generated_at=generated_at,
            )
            self.report_repository.create(report)

            # Shared transaction: an audit persistence failure here rolls
            # back the report metadata row too (the orphan-file cleanup
            # below still runs), rather than reporting a false SUCCESS.
            self.audit_service.append_event(
                event_type=AuditEventType.REPORT_GENERATED,
                category=AuditEventCategory.REPORT,
                outcome=AuditOutcome.SUCCESS,
                context=context,
                resource_type=AuditResourceType.REPORT,
                resource_id=report.id,
                scan_id=scan_id,
                metadata={
                    "format": report.format,
                    "vulnerability_count": report.vulnerability_count,
                    "ai_recommendations_included": report.ai_recommendations_included,
                    "file_size_bytes": report.file_size_bytes,
                },
            )
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            if final_path_published:
                # Metadata persistence failed after the file was published;
                # remove the orphaned file rather than leaving an untracked
                # artifact with no corresponding database record.
                final_path.unlink(missing_ok=True)
            self.audit_service.record_failure_safely(
                session=self.session,
                event_type=AuditEventType.REPORT_GENERATION_FAILED,
                category=AuditEventCategory.REPORT,
                context=context,
                resource_type=AuditResourceType.SCAN,
                resource_id=scan_id,
                scan_id=scan_id,
                metadata={"failure_category": type(exc).__name__},
            )
            raise

        logger.info(
            "Report generation completed",
            extra={
                "scan_id": str(scan_id),
                "report_id": str(report.id),
                "file_size_bytes": report.file_size_bytes,
            },
        )
        self.session.refresh(report)
        return report

    @staticmethod
    def _validate_pdf(path: Path) -> None:
        """Minimum practical validation that a genuine PDF was produced."""
        if not path.exists() or path.stat().st_size == 0:
            raise ReportRenderingException("Report rendering produced an empty file.")
        with path.open("rb") as handle:
            if handle.read(len(_PDF_SIGNATURE)) != _PDF_SIGNATURE:
                raise ReportRenderingException(
                    "Rendered output is not a valid PDF document."
                )

    def get_report(self, report_id: uuid.UUID) -> Report:
        """Retrieve report metadata by ID."""
        report = self.report_repository.get_by_id(report_id)
        if not report:
            raise NotFoundException(f"Report {report_id} not found.")
        return report

    def get_reports(
        self, skip: int = 0, limit: int = 50, scan_id: uuid.UUID | None = None
    ) -> tuple[Sequence[Report], int]:
        """Retrieve a paginated, optionally scan-filtered list of report metadata."""
        return self.report_repository.get_all(skip=skip, limit=limit, scan_id=scan_id)

    def get_report_file_path(
        self, report_id: uuid.UUID, audit_context: AuditContext | None = None
    ) -> Path:
        """Resolve the physical file path for a report, verifying it remains
        inside the configured storage root and actually exists on disk.

        This is the exclusive orchestration point for report downloads;
        the audit event is recorded here (never the file path or contents,
        only the report/scan identifiers).
        """
        report = self.get_report(report_id)
        root = self._storage_root().resolve()
        candidate = (root / report.file_name).resolve()

        if not candidate.is_relative_to(root):
            raise ReportStorageException(
                "Resolved report path is outside the storage root."
            )

        if not candidate.is_file():
            raise NotFoundException(
                f"Report file for {report_id} is missing from storage."
            )

        try:
            self.audit_service.append_event(
                event_type=AuditEventType.REPORT_DOWNLOADED,
                category=AuditEventCategory.REPORT,
                outcome=AuditOutcome.SUCCESS,
                context=audit_context or AuditContext.system(),
                resource_type=AuditResourceType.REPORT,
                resource_id=report.id,
                scan_id=report.scan_id,
                metadata={"format": report.format},
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            logger.error(
                "Audit subsystem failed to record a report download event; "
                "the download is unaffected.",
                extra={"report_id": str(report_id)},
                exc_info=True,
            )

        return candidate

    def delete_report(
        self, report_id: uuid.UUID, audit_context: AuditContext | None = None
    ) -> None:
        """Delete report metadata and its associated file."""
        report = self.get_report(report_id)
        root = self._storage_root().resolve()
        file_path = (root / report.file_name).resolve()
        report_format = report.format
        scan_id = report.scan_id

        try:
            self.report_repository.delete(report)
            self.audit_service.append_event(
                event_type=AuditEventType.REPORT_DELETED,
                category=AuditEventCategory.REPORT,
                outcome=AuditOutcome.SUCCESS,
                context=audit_context or AuditContext.system(),
                resource_type=AuditResourceType.REPORT,
                resource_id=report_id,
                scan_id=scan_id,
                metadata={"format": report_format},
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        if file_path.is_relative_to(root):
            file_path.unlink(missing_ok=True)
