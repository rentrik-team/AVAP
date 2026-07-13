import uuid
from unittest.mock import patch

import pytest

from app.core.enums import RiskLevel, RiskScope, ScanStatus, TargetType
from app.core.exceptions import NotFoundException
from app.models.asset import Asset
from app.models.risk_assessment import RiskAssessment
from app.models.scan_finding import ScanFinding
from app.models.scan_job import ScanJob
from app.models.service import NetworkService
from app.models.target import Target
from app.models.vulnerability import Vulnerability
from app.repositories.asset_repository import AssetRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.services.audit_service import AuditService
from app.services.risk_service import RiskService


@pytest.fixture
def target(db_session):
    t = Target(target="172.16.0.1", target_type=TargetType.IPV4)
    db_session.add(t)
    db_session.flush()
    return t


@pytest.fixture
def scan_job(db_session, target):
    job = ScanJob(target_id=target.id, status=ScanStatus.COMPLETED, scan_type="full")
    db_session.add(job)
    db_session.flush()
    return job


@pytest.fixture
def risk_service(db_session):
    return RiskService(
        session=db_session,
        risk_repository=RiskRepository(db_session),
        scan_repository=ScanRepository(db_session),
        asset_repository=AssetRepository(db_session),
        scan_finding_repository=ScanFindingRepository(db_session),
        audit_service=AuditService(AuditRepository(db_session)),
    )


def _seed_finding(db_session, scan_job, ip, severity_score, severity_rating, port=443):
    asset = Asset(ipv4=ip)
    db_session.add(asset)
    db_session.flush()

    service = NetworkService(
        asset_id=asset.id, port=port, protocol="tcp", service_name="https"
    )
    db_session.add(service)
    db_session.flush()

    vulnerability = Vulnerability(
        name=f"Vuln-{ip}-{port}",
        severity_score=severity_score,
        severity_rating=severity_rating,
    )
    db_session.add(vulnerability)
    db_session.flush()

    finding = ScanFinding(
        scan_id=scan_job.id,
        asset_id=asset.id,
        vulnerability_id=vulnerability.id,
        service_id=service.id,
    )
    db_session.add(finding)
    db_session.flush()

    return asset, vulnerability, finding


# --- Not found handling ---


def test_calculate_risk_for_missing_scan_raises(risk_service):
    with pytest.raises(NotFoundException):
        risk_service.calculate_risk_for_scan(uuid.uuid4())


def test_get_risk_by_asset_missing_asset_raises(risk_service):
    with pytest.raises(NotFoundException):
        risk_service.get_risk_by_asset(uuid.uuid4())


def test_get_risk_by_scan_missing_scan_raises(risk_service):
    with pytest.raises(NotFoundException):
        risk_service.get_risk_by_scan(uuid.uuid4())


def test_get_risk_by_scan_not_yet_calculated_raises(risk_service, scan_job):
    with pytest.raises(NotFoundException):
        risk_service.get_risk_by_scan(scan_job.id)


def test_get_summary_raises_when_none_calculated(risk_service):
    with pytest.raises(NotFoundException):
        risk_service.get_summary()


# --- Empty findings ---


def test_calculate_risk_empty_scan_persists_zero_score(
    db_session, risk_service, scan_job
):
    result = risk_service.calculate_risk_for_scan(scan_job.id)

    assert result.scope == RiskScope.SCAN
    assert result.risk_score == 0.0
    assert result.risk_level == RiskLevel.INFORMATIONAL


# --- Single finding ---


def test_calculate_risk_single_finding(db_session, risk_service, scan_job):
    asset, vulnerability, _ = _seed_finding(
        db_session, scan_job, "192.168.50.1", 7.0, "High"
    )

    scan_result = risk_service.calculate_risk_for_scan(scan_job.id)

    assert scan_result.risk_score == 7.0
    assert scan_result.risk_level == RiskLevel.HIGH

    vuln_records, _ = risk_service.risk_repository.get_all(
        scope=RiskScope.VULNERABILITY
    )
    assert len(vuln_records) == 1
    assert vuln_records[0].vulnerability_id == vulnerability.id

    asset_records, _ = risk_service.get_risk_by_asset(asset.id)
    assert len(asset_records) == 1
    assert asset_records[0].risk_score == 7.0


# --- Multiple findings, multiple assets ---


def test_calculate_risk_multiple_assets_scan_uses_worst_asset(
    db_session, risk_service, scan_job
):
    _seed_finding(db_session, scan_job, "192.168.60.1", 3.0, "Low", port=80)
    _seed_finding(db_session, scan_job, "192.168.60.2", 9.4, "Critical", port=443)

    scan_result = risk_service.calculate_risk_for_scan(scan_job.id)

    assert scan_result.risk_score == 9.4
    assert scan_result.risk_level == RiskLevel.CRITICAL


# --- Idempotent recalculation ---


def test_recalculation_with_unchanged_inputs_is_idempotent(
    db_session, risk_service, scan_job
):
    _seed_finding(db_session, scan_job, "192.168.70.1", 6.0, "Medium")

    first = risk_service.calculate_risk_for_scan(scan_job.id)
    second = risk_service.calculate_risk_for_scan(scan_job.id)

    assert first.id == second.id
    assert first.risk_score == second.risk_score

    count = (
        db_session.query(RiskAssessment)
        .filter(RiskAssessment.scope == RiskScope.SCAN)
        .count()
    )
    assert count == 1


def test_recalculation_after_finding_change_updates_score(
    db_session, risk_service, scan_job
):
    _seed_finding(db_session, scan_job, "192.168.80.1", 3.0, "Low")
    first = risk_service.calculate_risk_for_scan(scan_job.id)
    assert first.risk_score == 3.0

    _seed_finding(db_session, scan_job, "192.168.80.2", 9.9, "Critical")
    second = risk_service.calculate_risk_for_scan(scan_job.id)

    assert second.id == first.id
    assert second.risk_score == 9.9


# --- Assessment-level aggregation across scans ---


def test_assessment_summary_reflects_worst_scan(db_session, risk_service, target):
    scan_a = ScanJob(target_id=target.id, status=ScanStatus.COMPLETED, scan_type="full")
    scan_b = ScanJob(target_id=target.id, status=ScanStatus.COMPLETED, scan_type="full")
    db_session.add_all([scan_a, scan_b])
    db_session.flush()

    _seed_finding(db_session, scan_a, "192.168.90.1", 2.0, "Low")
    _seed_finding(db_session, scan_b, "192.168.90.2", 8.8, "High")

    risk_service.calculate_risk_for_scan(scan_a.id)
    risk_service.calculate_risk_for_scan(scan_b.id)

    summary = risk_service.get_summary()
    assert summary.risk_score == 8.8
    assert summary.risk_level == RiskLevel.HIGH


# --- Transaction rollback leaves no partial state ---


def test_failed_calculation_leaves_no_partial_risk_state(
    db_session, risk_service, scan_job
):
    """A failure partway through calculation must roll back every write from
    that attempt, leaving zero risk records rather than a partially
    calculated set (vulnerability rows without their asset/scan rollup).
    """
    scan_id = scan_job.id
    _seed_finding(db_session, scan_job, "192.168.100.1", 4.0, "Medium")

    with (
        patch.object(
            risk_service.risk_repository,
            "upsert",
            side_effect=RuntimeError("simulated failure"),
        ),
        pytest.raises(RuntimeError),
    ):
        risk_service.calculate_risk_for_scan(scan_id)

    remaining = (
        db_session.query(RiskAssessment)
        .filter(RiskAssessment.scan_id == scan_id)
        .count()
    )
    assert remaining == 0
