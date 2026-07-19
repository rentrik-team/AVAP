import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.audit.context import AuditContext
from app.core.enums import (
    AuditEventCategory,
    AuditEventType,
    AuditOutcome,
    AuditResourceType,
    RiskLevel,
    RiskScope,
)
from app.core.exceptions import NotFoundException
from app.models.risk_assessment import RiskAssessment
from app.repositories.asset_repository import AssetRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.risk_engine import rules
from app.risk_engine.aggregator import aggregate
from app.risk_engine.coordinator import calculate_scan_risk
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class RiskService:
    """Service layer for Risk Assessment business logic.

    Owns the transaction boundary for risk calculation and orchestrates the
    deterministic Risk Engine against persisted Module 05 data. The Risk
    Engine itself performs no database access and calls no external service.
    """

    def __init__(
        self,
        session: Session,
        risk_repository: RiskRepository,
        scan_repository: ScanRepository,
        asset_repository: AssetRepository,
        scan_finding_repository: ScanFindingRepository,
        audit_service: AuditService,
    ):
        self.session = session
        self.risk_repository = risk_repository
        self.scan_repository = scan_repository
        self.asset_repository = asset_repository
        self.scan_finding_repository = scan_finding_repository
        self.audit_service = audit_service

    def calculate_risk_for_scan(
        self, scan_id: uuid.UUID, audit_context: AuditContext | None = None
    ) -> RiskAssessment:
        """Calculate and persist deterministic risk for one scan.

        Recalculates vulnerability, asset, scan, and assessment-level risk
        within a single atomic transaction. Safe to call repeatedly: identical
        inputs produce identical persisted results, and each scope/entity
        combination is updated in place rather than duplicated.
        """
        context = audit_context or AuditContext.system()
        scan_job = self.scan_repository.get_by_id(scan_id)
        if not scan_job:
            raise NotFoundException(f"Scan job with ID {scan_id} not found.")

        findings = self.scan_finding_repository.get_by_scan(scan_id)
        calculation = calculate_scan_risk(findings)
        now = datetime.now(UTC)

        try:
            for finding_result in calculation.finding_results:
                finding = finding_result.finding
                result = finding_result.result
                self.risk_repository.upsert(
                    scope=RiskScope.VULNERABILITY,
                    risk_score=result.score,
                    risk_level=result.level,
                    calculation_version=rules.CALCULATION_VERSION,
                    calculated_at=now,
                    supporting_factors=result.supporting_factors,
                    scan_id=scan_id,
                    asset_id=finding.asset_id,
                    vulnerability_id=finding.vulnerability_id,
                    service_id=finding.service_id,
                )

            for asset_id, asset_result in calculation.asset_results.items():
                self.risk_repository.upsert(
                    scope=RiskScope.ASSET,
                    risk_score=asset_result.score,
                    risk_level=asset_result.level,
                    calculation_version=rules.CALCULATION_VERSION,
                    calculated_at=now,
                    supporting_factors=asset_result.supporting_factors,
                    scan_id=scan_id,
                    asset_id=asset_id,
                )

            scan_result = calculation.scan_result
            scan_record = self.risk_repository.upsert(
                scope=RiskScope.SCAN,
                risk_score=scan_result.score,
                risk_level=scan_result.level,
                calculation_version=rules.CALCULATION_VERSION,
                calculated_at=now,
                supporting_factors=scan_result.supporting_factors,
                scan_id=scan_id,
            )

            all_scan_scores = self.risk_repository.get_all_scan_scores()
            assessment_result = aggregate(list(all_scan_scores))
            self.risk_repository.upsert(
                scope=RiskScope.ASSESSMENT,
                risk_score=assessment_result.score,
                risk_level=assessment_result.level,
                calculation_version=rules.CALCULATION_VERSION,
                calculated_at=now,
                supporting_factors=assessment_result.supporting_factors,
            )

            # Shared transaction: if metadata validation or the audit
            # insert itself fails, this raises before commit and the
            # entire recalculation (including scan_record above) rolls
            # back rather than being reported as successful.
            self.audit_service.append_event(
                event_type=AuditEventType.RISK_CALCULATION_COMPLETED,
                category=AuditEventCategory.RISK,
                outcome=AuditOutcome.SUCCESS,
                context=context,
                resource_type=AuditResourceType.RISK_ASSESSMENT,
                resource_id=scan_record.id,
                scan_id=scan_id,
                metadata={
                    "risk_score": scan_result.score,
                    "risk_level": scan_result.level.value,
                    "calculation_version": rules.CALCULATION_VERSION,
                },
            )

            self.session.commit()
            logger.info(
                "Risk calculation completed",
                extra={
                    "scan_id": str(scan_id),
                    "vulnerability_findings": len(calculation.finding_results),
                    "assets_assessed": len(calculation.asset_results),
                    "scan_risk_score": scan_result.score,
                    "calculation_version": rules.CALCULATION_VERSION,
                },
            )
            self.session.refresh(scan_record)
            return scan_record

        except Exception as exc:
            logger.error(
                f"Risk calculation failed, rolling back transaction: {exc}",
                extra={"scan_id": str(scan_id)},
                exc_info=True,
            )
            self.session.rollback()

            # Record the failure event in a fresh transaction so it survives
            # the rollback above; never raised in place of the original
            # exception.
            self.audit_service.record_failure_safely(
                session=self.session,
                event_type=AuditEventType.RISK_CALCULATION_FAILED,
                category=AuditEventCategory.RISK,
                context=context,
                resource_type=AuditResourceType.SCAN,
                resource_id=scan_id,
                scan_id=scan_id,
                metadata={"failure_category": type(exc).__name__},
            )
            raise

    def get_risk_assessments(
        self,
        skip: int = 0,
        limit: int = 50,
        scope: RiskScope | None = None,
        risk_level: RiskLevel | None = None,
        scan_id: uuid.UUID | None = None,
    ) -> tuple[Sequence[RiskAssessment], int]:
        """Retrieve a paginated, filtered list of risk assessments."""
        return self.risk_repository.get_all(
            skip=skip, limit=limit, scope=scope, risk_level=risk_level, scan_id=scan_id
        )

    def get_risk_by_asset(
        self, asset_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> tuple[Sequence[RiskAssessment], int]:
        """Retrieve the paginated ASSET-scope risk history for one asset."""
        asset = self.asset_repository.get_by_id(asset_id)
        if not asset:
            raise NotFoundException(f"Asset with ID {asset_id} not found.")
        return self.risk_repository.get_by_asset(asset_id, skip=skip, limit=limit)

    def get_risk_by_scan(self, scan_id: uuid.UUID) -> RiskAssessment:
        """Retrieve the SCAN-scope risk assessment for one scan."""
        scan_job = self.scan_repository.get_by_id(scan_id)
        if not scan_job:
            raise NotFoundException(f"Scan job with ID {scan_id} not found.")

        risk = self.risk_repository.get_by_scan(scan_id)
        if not risk:
            raise NotFoundException(
                f"Risk assessment has not yet been calculated for scan {scan_id}."
            )
        return risk

    def get_summary(self) -> RiskAssessment:
        """Retrieve the overall assessment-level risk summary."""
        summary = self.risk_repository.get_assessment()
        if not summary:
            raise NotFoundException("No risk assessment has been calculated yet.")
        return summary
