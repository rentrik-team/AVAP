import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.config import Settings
from app.core.enums import ScanStatus, TargetType
from app.core.exceptions import (
    InsufficientReportDataException,
    NotFoundException,
    ReportRenderingException,
)
from app.models.report import Report
from app.models.scan_job import ScanJob
from app.models.target import Target
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
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.audit_service import AuditService
from app.services.inventory_service import InventoryService
from app.services.report_service import ReportService
from app.services.risk_service import RiskService


def _settings(tmp_path: Path) -> Settings:
    return Settings(_env_file=None, report_output_directory=str(tmp_path))


def _service(db_session, tmp_path: Path) -> ReportService:
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
        audit_service=AuditService(AuditRepository(db_session)),
        settings=_settings(tmp_path),
    )


def _seed_scan_with_findings(db_session, ipv4="203.0.113.30", calculate_risk=True):
    target = Target(target=ipv4, target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()
    scan_job = ScanJob(target_id=target.id, status=ScanStatus.RUNNING, scan_type="full")
    db_session.add(scan_job)
    db_session.flush()

    audit_service = AuditService(AuditRepository(db_session))
    inventory_service = InventoryService(
        db_session,
        AssetRepository(db_session),
        VulnerabilityRepository(db_session),
        ScanRepository(db_session),
        audit_service,
    )
    vuln = ParsedVulnerability(
        name="Outdated Service",
        severity_score=8.0,
        severity_rating="High",
        cve="CVE-2024-2000",
    )
    service = ParsedService(
        port=443, protocol="tcp", service_name="https", vulnerabilities=[vuln]
    )
    host = ParsedHost(ipv4=ipv4, services=[service])
    package = AssessmentPackage(
        scan_id=scan_job.id, scanner_type="OPENVAS", parsed_hosts=[host]
    )
    inventory_service.process_assessment_package(package)

    if calculate_risk:
        risk_service = RiskService(
            session=db_session,
            risk_repository=RiskRepository(db_session),
            scan_repository=ScanRepository(db_session),
            asset_repository=AssetRepository(db_session),
            scan_finding_repository=ScanFindingRepository(db_session),
            audit_service=audit_service,
        )
        risk_service.calculate_risk_for_scan(scan_job.id)

    return scan_job


# --- Successful generation ---


def test_generate_report_success(db_session, tmp_path):
    scan_job = _seed_scan_with_findings(db_session)
    service = _service(db_session, tmp_path)

    report = service.generate_report(scan_job.id)

    assert report.scan_id == scan_job.id
    assert report.vulnerability_count == 1
    assert report.overall_risk_score == 8.0
    assert report.file_size_bytes > 0
    assert (tmp_path / report.file_name).exists()
    assert (tmp_path / report.file_name).read_bytes()[:5] == b"%PDF-"


def test_generate_report_without_ai_recommendation(db_session, tmp_path):
    scan_job = _seed_scan_with_findings(db_session)
    report = _service(db_session, tmp_path).generate_report(scan_job.id)
    assert report.ai_recommendations_included == 0


# --- Not found / insufficient data ---


def test_generate_report_missing_scan_raises(db_session, tmp_path):
    with pytest.raises(NotFoundException):
        _service(db_session, tmp_path).generate_report(uuid.uuid4())


def test_generate_report_missing_risk_context_raises(db_session, tmp_path):
    scan_job = _seed_scan_with_findings(db_session, calculate_risk=False)
    with pytest.raises(InsufficientReportDataException):
        _service(db_session, tmp_path).generate_report(scan_job.id)


def test_get_report_missing_raises(db_session, tmp_path):
    with pytest.raises(NotFoundException):
        _service(db_session, tmp_path).get_report(uuid.uuid4())


# --- Repeated generation / history preservation ---


def test_repeated_generation_creates_new_immutable_report(db_session, tmp_path):
    scan_job = _seed_scan_with_findings(db_session)
    service = _service(db_session, tmp_path)

    first = service.generate_report(scan_job.id)
    second = service.generate_report(scan_job.id)

    assert first.id != second.id
    assert (tmp_path / first.file_name).exists()
    assert (tmp_path / second.file_name).exists()

    items, total = service.get_reports(scan_id=scan_job.id)
    assert total == 2


# --- Renderer failure ---


def test_generate_report_renderer_failure_leaves_no_partial_file(db_session, tmp_path):
    scan_job = _seed_scan_with_findings(db_session)
    service = _service(db_session, tmp_path)

    with (
        patch(
            "app.services.report_service.render_pdf", side_effect=RuntimeError("boom")
        ),
        pytest.raises(ReportRenderingException),
    ):
        service.generate_report(scan_job.id)

    assert list(tmp_path.glob("*.pdf")) == []
    assert list(tmp_path.glob("*.tmp")) == []
    remaining = db_session.query(Report).filter(Report.scan_id == scan_job.id).count()
    assert remaining == 0


def test_generate_report_invalid_pdf_signature_rejected(db_session, tmp_path):
    scan_job = _seed_scan_with_findings(db_session)
    service = _service(db_session, tmp_path)

    def _write_garbage(report_data, output_path):
        output_path.write_bytes(b"not a pdf")

    with (
        patch("app.services.report_service.render_pdf", side_effect=_write_garbage),
        pytest.raises(ReportRenderingException),
    ):
        service.generate_report(scan_job.id)

    assert list(tmp_path.glob("*.pdf")) == []


def test_previous_valid_report_survives_failed_regeneration(db_session, tmp_path):
    scan_job = _seed_scan_with_findings(db_session)
    service = _service(db_session, tmp_path)

    baseline = service.generate_report(scan_job.id)
    baseline_path = tmp_path / baseline.file_name
    assert baseline_path.exists()

    with (
        patch(
            "app.services.report_service.render_pdf", side_effect=RuntimeError("boom")
        ),
        pytest.raises(ReportRenderingException),
    ):
        service.generate_report(scan_job.id)

    assert baseline_path.exists()
    fetched = service.get_report(baseline.id)
    assert fetched.id == baseline.id


# --- Metadata persistence failure leaves no orphan file ---


def test_metadata_persistence_failure_removes_orphan_file(db_session, tmp_path):
    scan_job = _seed_scan_with_findings(db_session)
    service = _service(db_session, tmp_path)

    with (
        patch.object(
            service.report_repository, "create", side_effect=RuntimeError("db down")
        ),
        pytest.raises(RuntimeError),
    ):
        service.generate_report(scan_job.id)

    assert list(tmp_path.glob("*.pdf")) == []
    remaining = db_session.query(Report).filter(Report.scan_id == scan_job.id).count()
    assert remaining == 0


# --- File storage security ---


def test_generate_report_uses_server_generated_filename(db_session, tmp_path):
    scan_job = _seed_scan_with_findings(db_session)
    report = _service(db_session, tmp_path).generate_report(scan_job.id)

    assert report.file_name == f"report_{report.id}.pdf"
    assert ".." not in report.file_name
    assert "/" not in report.file_name and "\\" not in report.file_name


def test_get_report_file_path_stays_within_storage_root(db_session, tmp_path):
    scan_job = _seed_scan_with_findings(db_session)
    service = _service(db_session, tmp_path)
    report = service.generate_report(scan_job.id)

    resolved = service.get_report_file_path(report.id)
    assert resolved.is_relative_to(tmp_path.resolve())


def test_get_report_file_path_missing_file_raises_not_found(db_session, tmp_path):
    scan_job = _seed_scan_with_findings(db_session)
    service = _service(db_session, tmp_path)
    report = service.generate_report(scan_job.id)

    (tmp_path / report.file_name).unlink()

    with pytest.raises(NotFoundException):
        service.get_report_file_path(report.id)


def test_delete_report_removes_metadata_and_file(db_session, tmp_path):
    scan_job = _seed_scan_with_findings(db_session)
    service = _service(db_session, tmp_path)
    report = service.generate_report(scan_job.id)
    file_path = tmp_path / report.file_name
    assert file_path.exists()

    service.delete_report(report.id)

    assert not file_path.exists()
    with pytest.raises(NotFoundException):
        service.get_report(report.id)
