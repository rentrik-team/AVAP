import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.enums import RiskLevel, RiskScope, ScanStatus, TargetType
from app.models.ai_recommendation import AIRecommendation
from app.models.asset import Asset
from app.models.report import Report
from app.models.risk_assessment import RiskAssessment
from app.models.scan_finding import ScanFinding
from app.models.scan_job import ScanJob
from app.models.target import Target
from app.models.vulnerability import Vulnerability
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.risk_repository import RiskRepository
from app.services.dashboard_service import DashboardService


@pytest.fixture
def service(db_session):
    return DashboardService(
        dashboard_repository=DashboardRepository(db_session),
        risk_repository=RiskRepository(db_session),
        report_repository=ReportRepository(db_session),
    )


def _target(db_session, ip):
    t = Target(target=ip, target_type=TargetType.IPV4)
    db_session.add(t)
    db_session.flush()
    return t


def _scan(db_session, target, status=ScanStatus.COMPLETED, **kw):
    job = ScanJob(target_id=target.id, status=status, scan_type="full", **kw)
    db_session.add(job)
    db_session.flush()
    return job


def _asset(db_session, ip, hostname=None):
    a = Asset(ipv4=ip, hostname=hostname)
    db_session.add(a)
    db_session.flush()
    return a


def _vuln(db_session, name, severity_rating, cve=None, severity_score=5.0):
    v = Vulnerability(
        name=name,
        severity_rating=severity_rating,
        severity_score=severity_score,
        cve=cve,
    )
    db_session.add(v)
    db_session.flush()
    return v


def _finding(db_session, scan, asset, vuln=None, service=None):
    f = ScanFinding(
        scan_id=scan.id,
        asset_id=asset.id,
        vulnerability_id=vuln.id if vuln else None,
        service_id=service.id if service else None,
    )
    db_session.add(f)
    db_session.flush()
    return f


def _risk(
    db_session,
    scope,
    score,
    level,
    scan=None,
    asset=None,
    vuln=None,
    calculated_at=None,
):
    ra = RiskAssessment(
        scope=scope,
        risk_score=score,
        risk_level=level,
        calculation_version="1.0.0",
        calculated_at=calculated_at or datetime.now(UTC),
        supporting_factors={},
        scan_id=scan.id if scan else None,
        asset_id=asset.id if asset else None,
        vulnerability_id=vuln.id if vuln else None,
    )
    db_session.add(ra)
    db_session.flush()
    return ra


def _recommendation(
    db_session, vuln, risk_assessment, generated_at, provider="openrouter", model="m1"
):
    rec = AIRecommendation(
        vulnerability_id=vuln.id,
        risk_assessment_id=risk_assessment.id,
        provider=provider,
        model=model,
        prompt_version="1.0.0",
        summary="s",
        explanation="e",
        remediation_steps=["a"],
        validation_steps=["b"],
        cautions=["c"],
        generated_at=generated_at,
    )
    db_session.add(rec)
    db_session.flush()
    return rec


def _report(db_session, scan, generated_at, report_format="PDF", **kw):
    defaults = {
        "scan_id": scan.id,
        "format": report_format,
        "report_template_version": "1.0.0",
        "risk_calculation_version": "1.0.0",
        "source_risk_calculated_at": generated_at,
        "overall_risk_score": 5.0,
        "overall_risk_level": RiskLevel.MEDIUM,
        "vulnerability_count": 1,
        "ai_recommendations_included": 0,
        "file_name": f"report_{uuid.uuid4()}.pdf",
        "file_size_bytes": 100,
        "generated_at": generated_at,
    }
    defaults.update(kw)
    r = Report(**defaults)
    db_session.add(r)
    db_session.flush()
    return r


# --- Empty system state ---


def test_summary_empty_state(service):
    summary = service.get_summary()
    assert summary.total_targets == 0
    assert summary.total_scans == 0
    assert summary.total_assets == 0
    assert summary.unique_vulnerability_count == 0
    assert summary.critical_vulnerability_count == 0
    assert summary.total_reports_generated == 0
    assert summary.overall_risk_score == 0.0
    assert summary.overall_risk_level == RiskLevel.INFORMATIONAL
    assert summary.high_risk_asset_count == 0


def test_asset_statistics_empty_state(service):
    stats = service.get_asset_statistics(limit=10)
    assert stats.total_assets == 0
    assert stats.total_network_services == 0
    assert stats.recently_discovered_assets == []


def test_vulnerability_statistics_empty_state(service):
    stats = service.get_vulnerability_statistics()
    assert stats.unique_vulnerability_count == 0
    assert stats.finding_count == 0
    assert stats.severity_distribution.critical == 0


def test_risk_statistics_empty_state(service):
    stats = service.get_risk_statistics(top_limit=10)
    assert stats.overall_risk_score == 0.0
    assert stats.overall_risk_level == RiskLevel.INFORMATIONAL
    assert stats.top_risk_assets == []
    assert stats.top_risk_vulnerabilities == []


def test_scan_statistics_empty_state(service):
    stats = service.get_scan_statistics(limit=10)
    assert stats.total_scans == 0
    assert stats.scan_success_rate_percent == 0.0
    assert stats.average_scan_duration_seconds is None
    assert stats.recent_scans == []


def test_report_statistics_empty_state(service):
    stats = service.get_report_statistics(limit=10)
    assert stats.total_reports_generated == 0
    assert stats.reports_by_format == {}
    assert stats.latest_report_generated_at is None
    assert stats.recent_reports == []


def test_ai_statistics_empty_state(service):
    stats = service.get_ai_statistics()
    assert stats.total_recommendations == 0
    assert stats.eligible_vulnerability_risk_count == 0
    assert stats.current_recommendation_count == 0
    assert stats.missing_recommendation_count == 0
    assert stats.remediation_coverage_percent == 0.0


# --- Populated system state: authoritative source separation ---


def test_severity_distribution_uses_vulnerability_not_risk_level(db_session, service):
    """Vulnerability.severity_rating drives severity distribution; a HIGH
    deterministic risk score on a Medium-severity vulnerability must not
    shift it into the Critical/High severity bucket.
    """
    target = _target(db_session, "10.100.0.1")
    scan = _scan(db_session, target)
    asset = _asset(db_session, "10.100.0.1")
    vuln = _vuln(db_session, "Medium Severity Vuln", "Medium")
    _finding(db_session, scan, asset, vuln=vuln)
    _risk(
        db_session,
        RiskScope.VULNERABILITY,
        9.5,
        RiskLevel.CRITICAL,
        scan=scan,
        asset=asset,
        vuln=vuln,
    )

    vuln_stats = service.get_vulnerability_statistics()
    assert vuln_stats.severity_distribution.medium == 1
    assert vuln_stats.severity_distribution.critical == 0


def test_unknown_severity_rating_does_not_inflate_known_buckets(db_session, service):
    _vuln(db_session, "Weird", "TotallyUnknownRating")
    stats = service.get_vulnerability_statistics()
    assert stats.severity_distribution.critical == 0
    assert stats.severity_distribution.high == 0
    assert stats.unique_vulnerability_count == 1


def test_asset_risk_differs_from_vulnerability_risk_in_top_lists(db_session, service):
    target = _target(db_session, "10.101.0.1")
    scan = _scan(db_session, target)
    asset = _asset(db_session, "10.101.0.1")
    vuln = _vuln(db_session, "Some Vuln", "High", cve="CVE-2024-5000")

    _risk(db_session, RiskScope.ASSET, 3.0, RiskLevel.LOW, scan=scan, asset=asset)
    _risk(
        db_session,
        RiskScope.VULNERABILITY,
        8.5,
        RiskLevel.HIGH,
        scan=scan,
        asset=asset,
        vuln=vuln,
    )

    stats = service.get_risk_statistics(top_limit=10)
    assert stats.top_risk_assets[0].risk_score == 3.0
    assert stats.top_risk_vulnerabilities[0].risk_score == 8.5


def test_high_risk_asset_count_uses_worst_asset_scope_risk(db_session, service):
    target = _target(db_session, "10.102.0.1")
    scan1 = _scan(db_session, target)
    scan2 = _scan(db_session, target)
    asset = _asset(db_session, "10.102.0.1")

    _risk(db_session, RiskScope.ASSET, 2.0, RiskLevel.LOW, scan=scan1, asset=asset)
    _risk(db_session, RiskScope.ASSET, 8.0, RiskLevel.HIGH, scan=scan2, asset=asset)

    summary = service.get_summary()
    assert summary.high_risk_asset_count == 1


def test_current_recommendation_excludes_stale(db_session, service):
    target = _target(db_session, "10.103.0.1")
    scan = _scan(db_session, target)
    asset = _asset(db_session, "10.103.0.1")
    vuln_current = _vuln(db_session, "Current", "High", cve="CVE-2024-6000")
    vuln_stale = _vuln(db_session, "Stale", "Medium", cve="CVE-2024-6001")

    now = datetime.now(UTC)
    risk_current = _risk(
        db_session,
        RiskScope.VULNERABILITY,
        7.0,
        RiskLevel.HIGH,
        scan=scan,
        asset=asset,
        vuln=vuln_current,
        calculated_at=now,
    )
    risk_stale = _risk(
        db_session,
        RiskScope.VULNERABILITY,
        5.0,
        RiskLevel.MEDIUM,
        scan=scan,
        asset=asset,
        vuln=vuln_stale,
        calculated_at=now,
    )
    _recommendation(db_session, vuln_current, risk_current, now + timedelta(minutes=1))
    _recommendation(db_session, vuln_stale, risk_stale, now - timedelta(minutes=1))

    stats = service.get_ai_statistics()
    assert stats.eligible_vulnerability_risk_count == 2
    assert stats.current_recommendation_count == 1
    assert stats.missing_recommendation_count == 1
    assert stats.remediation_coverage_percent == 50.0


def test_zero_denominator_coverage_is_zero_not_error(service):
    stats = service.get_ai_statistics()
    assert stats.remediation_coverage_percent == 0.0


def test_report_statistics_from_metadata_not_filesystem(db_session, service):
    target = _target(db_session, "10.104.0.1")
    scan = _scan(db_session, target)
    _report(db_session, scan, datetime.now(UTC), format="PDF")

    stats = service.get_report_statistics(limit=10)
    assert stats.total_reports_generated == 1
    assert stats.reports_by_format == {"PDF": 1}
    assert len(stats.recent_reports) == 1


def test_recent_scans_use_persisted_lifecycle_fields(db_session, service):
    target = _target(db_session, "10.105.0.1")
    started = datetime.now(UTC) - timedelta(minutes=10)
    completed = datetime.now(UTC)
    _scan(
        db_session,
        target,
        status=ScanStatus.COMPLETED,
        started_at=started,
        completed_at=completed,
        execution_duration=600.0,
    )

    stats = service.get_scan_statistics(limit=10)
    scan_entry = stats.recent_scans[0]
    assert scan_entry.status == ScanStatus.COMPLETED
    assert scan_entry.execution_duration_seconds == 600.0
    assert scan_entry.target == "10.105.0.1"


def test_scan_success_rate_uses_terminal_scans_only(db_session, service):
    target = _target(db_session, "10.106.0.1")
    _scan(db_session, target, status=ScanStatus.COMPLETED)
    _scan(db_session, target, status=ScanStatus.FAILED)
    _scan(db_session, target, status=ScanStatus.RUNNING)
    _scan(db_session, target, status=ScanStatus.PENDING)

    stats = service.get_scan_statistics(limit=10)
    assert stats.scan_success_rate_percent == 50.0


# --- Deterministic response for identical persisted state ---


def test_summary_is_deterministic_for_identical_state(db_session, service):
    target = _target(db_session, "10.107.0.1")
    _scan(db_session, target)
    first = service.get_summary()
    second = service.get_summary()
    assert first.total_scans == second.total_scans
    assert first.total_targets == second.total_targets
