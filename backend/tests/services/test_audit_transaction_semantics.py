"""Transaction semantics tests for Module 10's integration into Modules
01/02/05/06/07/08: SUCCESS events must represent a truly committed business
action, FAILURE events must survive the business rollback they document,
and an audit persistence failure during a shared-transaction SUCCESS path
must roll back the business action rather than reporting a false SUCCESS.
"""

import json
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from app.ai.provider import AIProviderResponse
from app.core.enums import (
    AuditEventType,
    AuditOutcome,
    RiskScope,
    ScanStatus,
    TargetType,
)
from app.core.exceptions import AIProviderException, ReportRenderingException
from app.models.ai_recommendation import AIRecommendation
from app.models.asset import Asset
from app.models.audit_event import AuditEvent
from app.models.report import Report
from app.models.risk_assessment import RiskAssessment
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.models.vulnerability import Vulnerability
from app.parsers.models import (
    AssessmentPackage,
    ParsedHost,
    ParsedService,
    ParsedVulnerability,
)
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.network_service_repository import NetworkServiceRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.target_repository import TargetRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.schemas.scan import CreateScanRequest
from app.schemas.target import CreateTargetRequest
from app.services.ai_service import AIService
from app.services.audit_service import AuditService
from app.services.inventory_service import InventoryService
from app.services.report_service import ReportService
from app.services.risk_service import RiskService
from app.services.scan_service import ScanService
from app.services.target_service import TargetService


def _audit(db_session) -> AuditService:
    return AuditService(AuditRepository(db_session))


def _events(db_session, event_type=None, outcome=None):
    query = db_session.query(AuditEvent)
    if event_type is not None:
        query = query.filter(AuditEvent.event_type == event_type)
    if outcome is not None:
        query = query.filter(AuditEvent.outcome == outcome)
    return query.all()


# --- TargetService: shared transaction (repository flush + audit commit) ---


def test_target_created_success_event_persisted(db_session):
    audit_service = _audit(db_session)
    service = TargetService(TargetRepository(db_session), audit_service)

    target = service.create_target(CreateTargetRequest(target="198.51.100.1"))

    events = _events(db_session, AuditEventType.TARGET_CREATED)
    assert len(events) == 1
    assert events[0].outcome == AuditOutcome.SUCCESS
    assert events[0].resource_id == target.id


def test_target_created_audit_failure_rolls_back_target_creation(db_session):
    """TargetRepository.create() only flushes; TargetService owns the
    commit. If the audit insert fails inside the shared transaction, the
    whole transaction (including the new target) rolls back rather than
    reporting a false SUCCESS."""
    audit_service = _audit(db_session)
    service = TargetService(TargetRepository(db_session), audit_service)

    with (
        patch.object(
            audit_service, "append_event", side_effect=RuntimeError("audit db down")
        ),
        pytest.raises(RuntimeError),
    ):
        service.create_target(CreateTargetRequest(target="198.51.100.2"))

    assert TargetRepository(db_session).get_by_value("198.51.100.2") is None
    assert _events(db_session, AuditEventType.TARGET_CREATED) == []


def test_target_deleted_success_event_persisted(db_session):
    audit_service = _audit(db_session)
    service = TargetService(TargetRepository(db_session), audit_service)
    target = service.create_target(CreateTargetRequest(target="198.51.100.3"))

    service.delete_target(target.id)

    events = _events(db_session, AuditEventType.TARGET_DELETED)
    assert len(events) == 1
    assert events[0].resource_id == target.id


# --- ScanService: shared transaction (repository flush + audit commit) ---


def _scan_service(db_session, audit_service) -> ScanService:
    return ScanService(
        scan_repository=ScanRepository(db_session),
        target_repository=TargetRepository(db_session),
        audit_service=audit_service,
        scanner_engine=None,
    )


@pytest.fixture
def audit_target(db_session):
    target = Target(target="198.51.100.10", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.commit()
    return target


def test_scan_created_success_event_persisted(db_session, audit_target):
    audit_service = _audit(db_session)
    service = _scan_service(db_session, audit_service)

    scan_job = service.create_scan(
        CreateScanRequest(target_id=audit_target.id, scan_profile="full")
    )

    events = _events(db_session, AuditEventType.SCAN_CREATED)
    assert len(events) == 1
    assert events[0].outcome == AuditOutcome.SUCCESS
    assert events[0].resource_id == scan_job.id


def test_scan_created_audit_failure_rolls_back_scan_creation(db_session, audit_target):
    """ScanRepository.create() only flushes; ScanService owns the commit.
    If the audit insert fails inside the shared transaction, the whole
    transaction (including the new scan job) rolls back rather than
    reporting a false SUCCESS."""
    audit_service = _audit(db_session)
    service = _scan_service(db_session, audit_service)

    with (
        patch.object(
            audit_service, "append_event", side_effect=RuntimeError("audit db down")
        ),
        pytest.raises(RuntimeError),
    ):
        service.create_scan(
            CreateScanRequest(target_id=audit_target.id, scan_profile="full")
        )

    remaining = (
        db_session.query(ScanJob).filter(ScanJob.target_id == audit_target.id).count()
    )
    assert remaining == 0
    assert _events(db_session, AuditEventType.SCAN_CREATED) == []


def test_scan_deleted_success_event_persisted(db_session, audit_target):
    audit_service = _audit(db_session)
    service = _scan_service(db_session, audit_service)
    scan_job = service.create_scan(
        CreateScanRequest(target_id=audit_target.id, scan_profile="full")
    )

    service.delete_scan(scan_job.id)

    events = _events(db_session, AuditEventType.SCAN_DELETED)
    assert len(events) == 1
    assert events[0].resource_id == scan_job.id


# --- InventoryService: shared tx for SUCCESS, separate tx for FAILURE ---


def _package(scan_id, ipv4="10.10.10.1"):
    vuln = ParsedVulnerability(
        name="Test Vuln", severity_score=5.0, severity_rating="Medium"
    )
    service = ParsedService(
        port=80, protocol="tcp", service_name="http", vulnerabilities=[vuln]
    )
    host = ParsedHost(ipv4=ipv4, services=[service])
    return AssessmentPackage(scan_id=scan_id, scanner_type="NMAP", parsed_hosts=[host])


@pytest.fixture
def scan_job(db_session):
    target = Target(target="10.10.10.1", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()
    job = ScanJob(target_id=target.id, status=ScanStatus.RUNNING, scan_type="full")
    db_session.add(job)
    db_session.commit()
    return job


def test_inventory_processed_success_event_shares_transaction_with_findings(
    db_session, scan_job
):
    audit_service = _audit(db_session)
    service = InventoryService(
        db_session,
        AssetRepository(db_session),
        VulnerabilityRepository(db_session),
        ScanRepository(db_session),
        audit_service,
    )
    service.process_assessment_package(_package(scan_job.id))

    events = _events(db_session, AuditEventType.INVENTORY_PROCESSED)
    assert len(events) == 1
    assert events[0].outcome == AuditOutcome.SUCCESS
    assert db_session.query(Asset).count() == 1


def test_inventory_audit_failure_during_success_rolls_back_business_data(
    db_session, scan_job
):
    """If the audit insert itself fails inside the shared success
    transaction, the whole transaction (including the newly-processed
    asset) rolls back rather than reporting a false SUCCESS."""
    audit_service = _audit(db_session)
    service = InventoryService(
        db_session,
        AssetRepository(db_session),
        VulnerabilityRepository(db_session),
        ScanRepository(db_session),
        audit_service,
    )

    with (
        patch.object(
            audit_service,
            "append_event",
            side_effect=RuntimeError("audit insert failed"),
        ),
        pytest.raises(RuntimeError),
    ):
        service.process_assessment_package(_package(scan_job.id))

    # No asset from the failed attempt, and the scan was marked FAILED by
    # the existing rollback-recovery path (unaffected by Module 10).
    assert db_session.query(Asset).count() == 0
    refreshed = db_session.get(ScanJob, scan_job.id)
    assert refreshed.status == ScanStatus.FAILED


def test_inventory_processing_failed_event_survives_rollback(db_session, scan_job):
    audit_service = _audit(db_session)
    service = InventoryService(
        db_session,
        AssetRepository(db_session),
        VulnerabilityRepository(db_session),
        ScanRepository(db_session),
        audit_service,
    )

    with (
        patch.object(
            service, "_upsert_asset", side_effect=RuntimeError("simulated failure")
        ),
        pytest.raises(RuntimeError),
    ):
        service.process_assessment_package(_package(scan_job.id))

    events = _events(db_session, AuditEventType.INVENTORY_PROCESSING_FAILED)
    assert len(events) == 1
    assert events[0].outcome == AuditOutcome.FAILURE
    assert events[0].event_metadata["failure_category"] == "RuntimeError"


# --- RiskService ---


def _seed_finding(db_session, scan_job):
    asset = Asset(ipv4="10.20.0.1")
    db_session.add(asset)
    db_session.flush()
    vuln = Vulnerability(name="Risk Vuln", severity_score=6.0, severity_rating="Medium")
    db_session.add(vuln)
    db_session.flush()
    from app.models.scan_finding import ScanFinding

    finding = ScanFinding(
        scan_id=scan_job.id, asset_id=asset.id, vulnerability_id=vuln.id
    )
    db_session.add(finding)
    db_session.commit()
    return asset, vuln


@pytest.fixture
def risk_scan_job(db_session):
    target = Target(target="10.20.0.1", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()
    job = ScanJob(target_id=target.id, status=ScanStatus.COMPLETED, scan_type="full")
    db_session.add(job)
    db_session.flush()
    return job


def test_risk_calculation_completed_event_shares_transaction(db_session, risk_scan_job):
    _seed_finding(db_session, risk_scan_job)
    audit_service = _audit(db_session)
    service = RiskService(
        session=db_session,
        risk_repository=RiskRepository(db_session),
        scan_repository=ScanRepository(db_session),
        asset_repository=AssetRepository(db_session),
        scan_finding_repository=ScanFindingRepository(db_session),
        audit_service=audit_service,
    )

    scan_risk = service.calculate_risk_for_scan(risk_scan_job.id)

    events = _events(db_session, AuditEventType.RISK_CALCULATION_COMPLETED)
    assert len(events) == 1
    assert events[0].resource_id == scan_risk.id
    assert events[0].scan_id == risk_scan_job.id


def test_risk_calculation_audit_failure_rolls_back_risk_rows(db_session, risk_scan_job):
    _seed_finding(db_session, risk_scan_job)
    audit_service = _audit(db_session)
    service = RiskService(
        session=db_session,
        risk_repository=RiskRepository(db_session),
        scan_repository=ScanRepository(db_session),
        asset_repository=AssetRepository(db_session),
        scan_finding_repository=ScanFindingRepository(db_session),
        audit_service=audit_service,
    )

    with (
        patch.object(
            audit_service,
            "append_event",
            side_effect=RuntimeError("audit insert failed"),
        ),
        pytest.raises(RuntimeError),
    ):
        service.calculate_risk_for_scan(risk_scan_job.id)

    assert (
        db_session.query(RiskAssessment)
        .filter(RiskAssessment.scan_id == risk_scan_job.id)
        .count()
        == 0
    )


def test_risk_calculation_failed_event_survives_rollback(db_session, risk_scan_job):
    _seed_finding(db_session, risk_scan_job)
    audit_service = _audit(db_session)
    service = RiskService(
        session=db_session,
        risk_repository=RiskRepository(db_session),
        scan_repository=ScanRepository(db_session),
        asset_repository=AssetRepository(db_session),
        scan_finding_repository=ScanFindingRepository(db_session),
        audit_service=audit_service,
    )

    with (
        patch.object(
            service.risk_repository, "upsert", side_effect=RuntimeError("db failure")
        ),
        pytest.raises(RuntimeError),
    ):
        service.calculate_risk_for_scan(risk_scan_job.id)

    events = _events(db_session, AuditEventType.RISK_CALCULATION_FAILED)
    assert len(events) == 1
    assert events[0].outcome == AuditOutcome.FAILURE
    assert (
        db_session.query(RiskAssessment)
        .filter(RiskAssessment.scan_id == risk_scan_job.id)
        .count()
        == 0
    )


# --- AIService ---


class _FakeAIManager:
    def __init__(self, exc=None):
        self.exc = exc
        self.calls = 0

    def resolve_provider_name(self):
        return "openrouter"

    def resolve_model_name(self):
        return "fake-model"

    def generate(self, prompt):
        self.calls += 1
        if self.exc:
            raise self.exc
        return AIProviderResponse(
            content=json.dumps(
                {
                    "summary": "Upgrade.",
                    "explanation": "Outdated.",
                    "remediation_steps": ["Patch it."],
                    "validation_steps": ["Re-scan."],
                    "cautions": ["Schedule downtime."],
                }
            ),
            provider="openrouter",
            model="fake-model",
        )


@pytest.fixture
def vulnerability_risk(db_session, risk_scan_job):
    asset, vuln = _seed_finding(db_session, risk_scan_job)
    ra = RiskAssessment(
        scope=RiskScope.VULNERABILITY,
        risk_score=6.0,
        risk_level="MEDIUM",
        calculation_version="1.0.0",
        calculated_at=datetime.now(UTC),
        supporting_factors={},
        scan_id=risk_scan_job.id,
        asset_id=asset.id,
        vulnerability_id=vuln.id,
    )
    db_session.add(ra)
    db_session.commit()
    return ra


def _ai_service(db_session, audit_service, ai_manager):
    return AIService(
        session=db_session,
        ai_recommendation_repository=AIRecommendationRepository(db_session),
        risk_repository=RiskRepository(db_session),
        vulnerability_repository=VulnerabilityRepository(db_session),
        network_service_repository=NetworkServiceRepository(db_session),
        audit_service=audit_service,
        ai_manager=ai_manager,
    )


def test_ai_recommendation_generated_event_shares_transaction(
    db_session, vulnerability_risk
):
    audit_service = _audit(db_session)
    service = _ai_service(db_session, audit_service, _FakeAIManager())

    recommendation = service.generate_recommendation(vulnerability_risk.id)

    events = _events(db_session, AuditEventType.AI_RECOMMENDATION_GENERATED)
    assert len(events) == 1
    assert events[0].resource_id == recommendation.id
    assert events[0].event_metadata["provider"] == "openrouter"
    assert "remediation_steps" not in events[0].event_metadata
    assert "summary" not in events[0].event_metadata


def test_ai_recommendation_failed_event_on_provider_failure(
    db_session, vulnerability_risk
):
    audit_service = _audit(db_session)
    service = _ai_service(
        db_session,
        audit_service,
        _FakeAIManager(exc=AIProviderException("provider returned 401")),
    )

    with pytest.raises(AIProviderException):
        service.generate_recommendation(vulnerability_risk.id)

    events = _events(db_session, AuditEventType.AI_RECOMMENDATION_FAILED)
    assert len(events) == 1
    assert events[0].outcome == AuditOutcome.FAILURE
    assert events[0].event_metadata == {"failure_category": "AIProviderException"}
    assert db_session.query(AIRecommendation).count() == 0


def test_ai_recommendation_generated_no_duplicate_event_per_idempotent_call(
    db_session, vulnerability_risk
):
    """Calling generate_recommendation twice (second call idempotently
    reuses the existing current recommendation) must record exactly one
    audit event per call — never zero, never more than one per call, and
    never a duplicate solely from the idempotent short-circuit."""
    audit_service = _audit(db_session)
    manager = _FakeAIManager()
    service = _ai_service(db_session, audit_service, manager)

    service.generate_recommendation(vulnerability_risk.id)
    service.generate_recommendation(vulnerability_risk.id)

    assert manager.calls == 1  # provider only called once; second call was idempotent
    events = _events(db_session, AuditEventType.AI_RECOMMENDATION_GENERATED)
    assert len(events) == 2  # one audit event per service call


# --- ReportService ---


@pytest.fixture
def scan_with_calculated_risk(db_session):
    target = Target(target="10.30.0.1", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()
    scan_job = ScanJob(target_id=target.id, status=ScanStatus.RUNNING, scan_type="full")
    db_session.add(scan_job)
    db_session.flush()

    audit_service = _audit(db_session)
    inventory_service = InventoryService(
        db_session,
        AssetRepository(db_session),
        VulnerabilityRepository(db_session),
        ScanRepository(db_session),
        audit_service,
    )
    inventory_service.process_assessment_package(
        _package(scan_job.id, ipv4="10.30.0.1")
    )

    risk_service = RiskService(
        session=db_session,
        risk_repository=RiskRepository(db_session),
        scan_repository=ScanRepository(db_session),
        asset_repository=AssetRepository(db_session),
        scan_finding_repository=ScanFindingRepository(db_session),
        audit_service=audit_service,
    )
    risk_service.calculate_risk_for_scan(scan_job.id)
    return scan_job, audit_service


def _report_service(db_session, audit_service, tmp_path):
    from app.core.config import Settings

    return ReportService(
        session=db_session,
        report_repository=ReportRepository(db_session),
        scan_repository=ScanRepository(db_session),
        risk_repository=RiskRepository(db_session),
        asset_repository=AssetRepository(db_session),
        vulnerability_repository=VulnerabilityRepository(db_session),
        network_service_repository=NetworkServiceRepository(db_session),
        scan_finding_repository=ScanFindingRepository(db_session),
        ai_recommendation_repository=AIRecommendationRepository(db_session),
        audit_service=audit_service,
        settings=Settings(_env_file=None, report_output_directory=str(tmp_path)),
    )


def test_report_generated_event_shares_transaction(
    db_session, scan_with_calculated_risk, tmp_path
):
    scan_job, audit_service = scan_with_calculated_risk
    service = _report_service(db_session, audit_service, tmp_path)

    report = service.generate_report(scan_job.id)

    events = _events(db_session, AuditEventType.REPORT_GENERATED)
    assert len(events) == 1
    assert events[0].resource_id == report.id
    assert "file_name" not in events[0].event_metadata
    assert str(tmp_path) not in json.dumps(events[0].event_metadata)


def test_report_generation_failed_event_survives_rollback(
    db_session, scan_with_calculated_risk, tmp_path
):
    scan_job, audit_service = scan_with_calculated_risk
    service = _report_service(db_session, audit_service, tmp_path)

    with (
        patch(
            "app.services.report_service.render_pdf", side_effect=RuntimeError("boom")
        ),
        pytest.raises(ReportRenderingException),
    ):
        service.generate_report(scan_job.id)

    events = _events(db_session, AuditEventType.REPORT_GENERATION_FAILED)
    assert len(events) == 1
    assert events[0].outcome == AuditOutcome.FAILURE
    assert db_session.query(Report).count() == 0


def test_report_deleted_event_persisted(
    db_session, scan_with_calculated_risk, tmp_path
):
    scan_job, audit_service = scan_with_calculated_risk
    service = _report_service(db_session, audit_service, tmp_path)
    report = service.generate_report(scan_job.id)

    service.delete_report(report.id)

    events = _events(db_session, AuditEventType.REPORT_DELETED)
    assert len(events) == 1
    assert events[0].resource_id == report.id


def test_report_downloaded_event_persisted_without_path(
    db_session, scan_with_calculated_risk, tmp_path
):
    scan_job, audit_service = scan_with_calculated_risk
    service = _report_service(db_session, audit_service, tmp_path)
    report = service.generate_report(scan_job.id)

    service.get_report_file_path(report.id)

    events = _events(db_session, AuditEventType.REPORT_DOWNLOADED)
    assert len(events) == 1
    assert str(tmp_path) not in json.dumps(events[0].event_metadata)
    assert "file_name" not in events[0].event_metadata
