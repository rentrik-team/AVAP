"""Module 08 security tests: path traversal defense-in-depth, and the
Reporting Engine's database/AI independence boundaries.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.enums import ScanStatus, TargetType
from app.core.exceptions import ReportStorageException
from app.models.report import Report
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.network_service_repository import NetworkServiceRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.report_service import ReportService


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
        settings=Settings(_env_file=None, report_output_directory=str(tmp_path)),
    )


@pytest.fixture
def scan_job(db_session):
    target = Target(target="203.0.113.50", target_type=TargetType.IPV4)
    db_session.add(target)
    db_session.flush()
    job = ScanJob(target_id=target.id, status=ScanStatus.COMPLETED, scan_type="full")
    db_session.add(job)
    db_session.flush()
    return job


def _persist_report_with_filename(db_session, scan_job, file_name: str) -> Report:
    from app.core.enums import RiskLevel

    report = Report(
        scan_id=scan_job.id,
        format="PDF",
        report_template_version="1.0.0",
        risk_calculation_version="1.0.0",
        source_risk_calculated_at=datetime.now(UTC),
        overall_risk_score=5.0,
        overall_risk_level=RiskLevel.MEDIUM,
        vulnerability_count=1,
        ai_recommendations_included=0,
        file_name=file_name,
        file_size_bytes=10,
        generated_at=datetime.now(UTC),
    )
    db_session.add(report)
    db_session.commit()
    return report


# --- Path traversal defense-in-depth ---
# file_name is always server-generated in real operation; these tests prove
# the storage-root containment check itself is a genuine, active safeguard
# rather than a comment, should a stored value ever be anomalous.


@pytest.mark.parametrize(
    "malicious_name",
    [
        "../../etc/passwd",
        "..\\..\\Windows\\System32\\config\\SAM",
        "/etc/passwd",
        "C:\\Windows\\System32\\config\\SAM",
        "reports/../../../secret.pdf",
    ],
)
def test_get_report_file_path_rejects_traversal(
    db_session, tmp_path, scan_job, malicious_name
):
    report = _persist_report_with_filename(db_session, scan_job, malicious_name)
    service = _service(db_session, tmp_path)

    with pytest.raises(ReportStorageException):
        service.get_report_file_path(report.id)


def test_get_report_file_path_accepts_normal_server_filename(
    db_session, tmp_path, scan_job
):
    report = _persist_report_with_filename(
        db_session, scan_job, f"report_{report_id_placeholder()}.pdf"
    )
    service = _service(db_session, tmp_path)
    (tmp_path / report.file_name).write_bytes(b"%PDF-1.4 test")

    resolved = service.get_report_file_path(report.id)
    assert resolved.is_relative_to(tmp_path.resolve())


def report_id_placeholder() -> str:
    import uuid

    return str(uuid.uuid4())


# --- Reporting Engine independence: never calls AI, never calculates risk ---


def test_report_service_module_has_no_ai_provider_imports():
    import app.reporting.generator as generator_module
    import app.reporting.pdf as pdf_module
    import app.services.report_service as report_service_module

    for module in (report_service_module, generator_module, pdf_module):
        source = module.__file__
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        assert "openrouter" not in content.lower()
        assert "ai_manager" not in content.lower()
        assert "AIManager" not in content
