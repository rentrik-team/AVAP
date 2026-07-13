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
from app.models.service import NetworkService
from app.models.target import Target
from app.models.vulnerability import Vulnerability
from app.repositories.dashboard_repository import DashboardRepository


@pytest.fixture
def repository(db_session):
    return DashboardRepository(db_session)


def _target(db_session, ip):
    t = Target(target=ip, target_type=TargetType.IPV4)
    db_session.add(t)
    db_session.flush()
    return t


def _scan(db_session, target, status=ScanStatus.COMPLETED, created_at=None, **kw):
    job = ScanJob(target_id=target.id, status=status, scan_type="full", **kw)
    if created_at is not None:
        job.created_at = created_at
    db_session.add(job)
    db_session.flush()
    return job


def _asset(db_session, ip, hostname=None, created_at=None):
    a = Asset(ipv4=ip, hostname=hostname)
    if created_at is not None:
        a.created_at = created_at
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
    service=None,
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
        service_id=service.id if service else None,
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


# --- Empty database state ---


def test_empty_database_returns_zeroed_and_empty_aggregates(repository):
    assert repository.count_targets() == 0
    assert repository.count_scans() == 0
    assert repository.count_assets() == 0
    assert repository.count_network_services() == 0
    assert repository.count_vulnerabilities() == 0
    assert repository.count_scan_findings() == 0
    assert repository.count_ai_recommendations() == 0
    assert repository.get_scan_status_distribution() == {}
    assert repository.get_average_scan_duration_seconds() is None
    assert repository.get_recent_scans(10) == []
    assert repository.get_recently_discovered_assets(10) == []
    assert repository.get_vulnerability_severity_distribution() == {}
    assert repository.get_top_risk_assets(10) == []
    assert repository.get_asset_risk_level_distribution() == {}
    assert repository.get_top_risk_vulnerabilities(10) == []
    assert repository.get_affected_asset_counts([]) == {}
    assert repository.get_reports_by_format() == {}
    assert repository.get_latest_report_generated_at() is None
    assert repository.get_recommendations_by_provider() == {}
    assert repository.get_recommendations_by_model() == {}
    assert repository.get_recommendations_by_severity() == {}
    eligible, current = repository.get_remediation_coverage_counts()
    assert eligible == 0
    assert current == 0


# --- Vulnerability identity vs finding count (must never be confused) ---


def test_vulnerability_count_differs_from_finding_count(db_session, repository):
    target = _target(db_session, "10.90.0.1")
    scan = _scan(db_session, target)
    asset1 = _asset(db_session, "10.90.0.1")
    asset2 = _asset(db_session, "10.90.0.2")
    asset3 = _asset(db_session, "10.90.0.3")
    v1 = _vuln(db_session, "Vuln One", "Critical", cve="CVE-2024-0001")
    v2 = _vuln(db_session, "Vuln Two", "High", cve="CVE-2024-0002")

    _finding(db_session, scan, asset1, vuln=v1)
    _finding(db_session, scan, asset2, vuln=v1)
    _finding(db_session, scan, asset1, vuln=v2)
    _finding(db_session, scan, asset2, vuln=v2)
    service = NetworkService(
        asset_id=asset3.id, port=22, protocol="tcp", service_name="ssh"
    )
    db_session.add(service)
    db_session.flush()
    _finding(db_session, scan, asset3, service=service)

    assert repository.count_vulnerabilities() == 2
    assert repository.count_scan_findings() == 5


# --- Severity distribution: unrecognized values pass through untouched ---


def test_vulnerability_severity_distribution_raw_grouping(db_session, repository):
    _vuln(db_session, "A", "Critical")
    _vuln(db_session, "B", "Critical")
    _vuln(db_session, "C", "High")
    _vuln(db_session, "D", "None")
    _vuln(db_session, "E", "Bogus")

    dist = repository.get_vulnerability_severity_distribution()
    assert dist["Critical"] == 2
    assert dist["High"] == 1
    assert dist["None"] == 1
    assert dist["Bogus"] == 1


# --- Scan status distribution and duration ---


def test_scan_status_distribution_and_average_duration(db_session, repository):
    target = _target(db_session, "10.91.0.1")
    _scan(db_session, target, status=ScanStatus.COMPLETED, execution_duration=120.0)
    _scan(db_session, target, status=ScanStatus.COMPLETED, execution_duration=60.0)
    _scan(db_session, target, status=ScanStatus.FAILED)
    _scan(db_session, target, status=ScanStatus.RUNNING)

    dist = repository.get_scan_status_distribution()
    assert dist[ScanStatus.COMPLETED] == 2
    assert dist[ScanStatus.FAILED] == 1
    assert dist[ScanStatus.RUNNING] == 1

    avg = repository.get_average_scan_duration_seconds()
    assert avg == pytest.approx(90.0)


def test_average_scan_duration_none_when_no_durations_recorded(db_session, repository):
    target = _target(db_session, "10.91.0.2")
    _scan(db_session, target, status=ScanStatus.PENDING)
    assert repository.get_average_scan_duration_seconds() is None


def test_get_recent_scans_orders_desc_and_respects_limit(db_session, repository):
    target = _target(db_session, "10.92.0.1")
    now = datetime.now(UTC)
    _scan(db_session, target, created_at=now - timedelta(minutes=5))
    newest = _scan(db_session, target, created_at=now)

    recent = repository.get_recent_scans(1)
    assert len(recent) == 1
    assert recent[0].id == newest.id


# --- Recently discovered assets ---


def test_get_recently_discovered_assets_orders_desc_and_respects_limit(
    db_session, repository
):
    now = datetime.now(UTC)
    _asset(db_session, "10.93.0.1", created_at=now - timedelta(minutes=5))
    newest = _asset(db_session, "10.93.0.2", created_at=now)

    recent = repository.get_recently_discovered_assets(1)
    assert len(recent) == 1
    assert recent[0].id == newest.id


# --- Top risk assets: worst-per-asset ranking with deterministic tie-break ---


def test_get_top_risk_assets_ranks_worst_per_asset(db_session, repository):
    target = _target(db_session, "10.94.0.1")
    scan1 = _scan(db_session, target)
    scan2 = _scan(db_session, target)
    asset_a = _asset(db_session, "10.94.0.1")
    asset_b = _asset(db_session, "10.94.0.2")

    _risk(db_session, RiskScope.ASSET, 3.0, RiskLevel.LOW, scan=scan1, asset=asset_a)
    _risk(db_session, RiskScope.ASSET, 8.0, RiskLevel.HIGH, scan=scan2, asset=asset_a)
    _risk(
        db_session, RiskScope.ASSET, 9.5, RiskLevel.CRITICAL, scan=scan1, asset=asset_b
    )

    top = repository.get_top_risk_assets(10)
    assert len(top) == 2
    assert top[0].asset_id == asset_b.id
    assert top[0].risk_score == 9.5
    assert top[1].asset_id == asset_a.id
    assert top[1].risk_score == 8.0


def test_get_top_risk_assets_respects_limit(db_session, repository):
    target = _target(db_session, "10.94.0.3")
    scan = _scan(db_session, target)
    for i in range(3):
        asset = _asset(db_session, f"10.94.1.{i}")
        _risk(
            db_session, RiskScope.ASSET, float(i), RiskLevel.LOW, scan=scan, asset=asset
        )

    assert len(repository.get_top_risk_assets(2)) == 2


def test_get_asset_risk_level_distribution_counts_worst_per_asset_only(
    db_session, repository
):
    target = _target(db_session, "10.94.0.4")
    scan1 = _scan(db_session, target)
    scan2 = _scan(db_session, target)
    asset_a = _asset(db_session, "10.94.2.1")

    # Same asset assessed twice; only the worst (8.0/HIGH) should count.
    _risk(db_session, RiskScope.ASSET, 2.0, RiskLevel.LOW, scan=scan1, asset=asset_a)
    _risk(db_session, RiskScope.ASSET, 8.0, RiskLevel.HIGH, scan=scan2, asset=asset_a)

    dist = repository.get_asset_risk_level_distribution()
    assert dist[RiskLevel.HIGH] == 1
    assert RiskLevel.LOW not in dist


# --- Top risk vulnerabilities and affected asset counts ---


def test_get_top_risk_vulnerabilities_ranks_worst_per_vulnerability(
    db_session, repository
):
    target = _target(db_session, "10.95.0.1")
    scan = _scan(db_session, target)
    asset1 = _asset(db_session, "10.95.0.1")
    asset2 = _asset(db_session, "10.95.0.2")
    v1 = _vuln(db_session, "Vuln One", "Critical", cve="CVE-2024-1000")
    v2 = _vuln(db_session, "Vuln Two", "High", cve="CVE-2024-1001")

    _risk(
        db_session,
        RiskScope.VULNERABILITY,
        6.0,
        RiskLevel.MEDIUM,
        scan=scan,
        asset=asset1,
        vuln=v1,
    )
    _risk(
        db_session,
        RiskScope.VULNERABILITY,
        9.0,
        RiskLevel.CRITICAL,
        scan=scan,
        asset=asset2,
        vuln=v1,
    )
    _risk(
        db_session,
        RiskScope.VULNERABILITY,
        7.5,
        RiskLevel.HIGH,
        scan=scan,
        asset=asset1,
        vuln=v2,
    )

    top = repository.get_top_risk_vulnerabilities(10)
    assert len(top) == 2
    assert top[0].vulnerability_id == v1.id
    assert top[0].risk_score == 9.0
    assert top[1].vulnerability_id == v2.id

    counts = repository.get_affected_asset_counts([v1.id, v2.id])
    assert counts[v1.id] == 2
    assert counts[v2.id] == 1


def test_get_affected_asset_counts_empty_input_returns_empty_dict(repository):
    assert repository.get_affected_asset_counts([]) == {}


# --- Report statistics ---


def test_reports_by_format_and_latest_generated_at(db_session, repository):
    target = _target(db_session, "10.96.0.1")
    scan = _scan(db_session, target)
    now = datetime.now(UTC)
    _report(db_session, scan, now - timedelta(days=1))
    newest = _report(db_session, scan, now)

    dist = repository.get_reports_by_format()
    assert dist["PDF"] == 2
    # SQLite does not round-trip tzinfo; compare naive wall-clock values only.
    latest = repository.get_latest_report_generated_at()
    assert latest.replace(tzinfo=None) == newest.generated_at.replace(tzinfo=None)


# --- AI recommendation statistics and remediation coverage ---


def test_recommendations_by_provider_model_and_severity(db_session, repository):
    target = _target(db_session, "10.97.0.1")
    scan = _scan(db_session, target)
    asset = _asset(db_session, "10.97.0.1")
    vuln = _vuln(db_session, "Outdated OpenSSH", "High", cve="CVE-2024-2000")
    risk = _risk(
        db_session,
        RiskScope.VULNERABILITY,
        7.0,
        RiskLevel.HIGH,
        scan=scan,
        asset=asset,
        vuln=vuln,
    )
    _recommendation(
        db_session,
        vuln,
        risk,
        datetime.now(UTC),
        provider="openrouter",
        model="model-a",
    )

    assert repository.get_recommendations_by_provider() == {"openrouter": 1}
    assert repository.get_recommendations_by_model() == {"model-a": 1}
    assert repository.get_recommendations_by_severity() == {"High": 1}


def test_remediation_coverage_excludes_stale_recommendations(db_session, repository):
    target = _target(db_session, "10.98.0.1")
    scan = _scan(db_session, target)
    asset = _asset(db_session, "10.98.0.1")
    vuln_current = _vuln(db_session, "Current Vuln", "High", cve="CVE-2024-3000")
    vuln_stale = _vuln(db_session, "Stale Vuln", "Medium", cve="CVE-2024-3001")
    vuln_missing = _vuln(db_session, "Missing Vuln", "Low", cve="CVE-2024-3002")

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
    _risk(
        db_session,
        RiskScope.VULNERABILITY,
        2.0,
        RiskLevel.LOW,
        scan=scan,
        asset=asset,
        vuln=vuln_missing,
        calculated_at=now,
    )

    # Current: generated after calculation.
    _recommendation(db_session, vuln_current, risk_current, now + timedelta(minutes=5))
    # Stale: generated before the risk was (re)calculated.
    _recommendation(db_session, vuln_stale, risk_stale, now - timedelta(minutes=5))
    # vuln_missing has no recommendation at all.

    eligible, current = repository.get_remediation_coverage_counts()
    assert eligible == 3
    assert current == 1


# --- No mutation / no commit ---


def test_dashboard_queries_never_add_or_dirty_session_state(db_session, repository):
    target = _target(db_session, "10.99.0.1")
    scan = _scan(db_session, target)
    asset = _asset(db_session, "10.99.0.1")
    _finding(db_session, scan, asset)

    db_session.expire_all()
    repository.count_targets()
    repository.count_scans()
    repository.get_scan_status_distribution()
    repository.get_recent_scans(5)
    repository.get_top_risk_assets(5)
    repository.get_asset_risk_level_distribution()
    repository.get_remediation_coverage_counts()

    assert len(db_session.new) == 0
    assert len(db_session.dirty) == 0
