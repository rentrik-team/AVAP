import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from sqlalchemy import select, func

from app.core.enums import ScanStatus, ScannerType, TargetType
from app.core.exceptions import NotFoundException
from app.models.target import Target
from app.models.scan_job import ScanJob
from app.models.asset import Asset
from app.models.service import NetworkService
from app.models.vulnerability import Vulnerability
from app.models.scan_finding import ScanFinding
from app.repositories.asset_repository import AssetRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.repositories.scan_repository import ScanRepository
from app.services.audit_service import AuditService
from app.services.inventory_service import InventoryService
from app.parsers.models import AssessmentPackage, ParsedHost, ParsedService, ParsedVulnerability


@pytest.fixture
def target(db_session):
    t = Target(target="192.168.1.1", target_type=TargetType.IPV4)
    db_session.add(t)
    db_session.flush()
    return t


@pytest.fixture
def scan_job(db_session, target):
    job = ScanJob(
        target_id=target.id,
        status=ScanStatus.RUNNING,
        scan_type="full",
        started_at=datetime.now(timezone.utc)
    )
    db_session.add(job)
    # Commit (not just flush): in production, ScanRepository.create() always
    # commits a scan job before InventoryService ever processes it, so a scan
    # job is durably persisted by the time processing begins. Only flushing
    # here would make it disappear on InventoryService's own rollback-on-
    # failure path, which does not reflect real behavior.
    db_session.commit()
    return job


@pytest.fixture
def inventory_service(db_session):
    asset_repo = AssetRepository(db_session)
    vuln_repo = VulnerabilityRepository(db_session)
    scan_repo = ScanRepository(db_session)
    audit_service = AuditService(AuditRepository(db_session))
    return InventoryService(db_session, asset_repo, vuln_repo, scan_repo, audit_service)


def _make_package(scan_id, hosts=None):
    """Helper to build an AssessmentPackage."""
    return AssessmentPackage(
        scan_id=scan_id,
        scanner_type=ScannerType.NMAP,
        parsed_hosts=hosts or []
    )


# --- ScanJob Resolution ---

def test_missing_scan_job_raises(inventory_service):
    """NotFoundException when scan_id doesn't exist."""
    pkg = _make_package(scan_id=uuid.uuid4())
    with pytest.raises(NotFoundException):
        inventory_service.process_assessment_package(pkg)


# --- Asset Creation ---

def test_new_asset_created(db_session, inventory_service, scan_job):
    host = ParsedHost(ipv4="10.0.0.1", hostname="host-a", operating_system="Linux")
    pkg = _make_package(scan_job.id, [host])

    inventory_service.process_assessment_package(pkg)

    asset = db_session.execute(select(Asset).where(Asset.ipv4 == "10.0.0.1")).scalar_one()
    assert asset.hostname == "host-a"
    assert asset.operating_system == "Linux"


# --- Asset Reuse ---

def test_existing_asset_reused(db_session, inventory_service, scan_job, target):
    # Pre-create asset
    existing = Asset(ipv4="10.0.0.2", hostname="old-host", operating_system="FreeBSD")
    db_session.add(existing)
    db_session.flush()

    host = ParsedHost(ipv4="10.0.0.2", hostname="new-host", operating_system="FreeBSD 14")
    pkg = _make_package(scan_job.id, [host])

    inventory_service.process_assessment_package(pkg)

    # Should still be one asset with that IP
    count = db_session.execute(select(func.count(Asset.id)).where(Asset.ipv4 == "10.0.0.2")).scalar()
    assert count == 1

    db_session.expire_all()
    asset = db_session.execute(select(Asset).where(Asset.ipv4 == "10.0.0.2")).scalar_one()
    assert asset.hostname == "new-host"
    assert asset.operating_system == "FreeBSD 14"


# --- Asset Metadata Non-Overwrite ---

def test_asset_metadata_not_overwritten_with_empty(db_session, inventory_service, scan_job):
    existing = Asset(ipv4="10.0.0.3", hostname="good-host", operating_system="Debian")
    db_session.add(existing)
    db_session.flush()

    host = ParsedHost(ipv4="10.0.0.3", hostname="", operating_system=None)
    pkg = _make_package(scan_job.id, [host])

    inventory_service.process_assessment_package(pkg)

    db_session.expire_all()
    asset = db_session.execute(select(Asset).where(Asset.ipv4 == "10.0.0.3")).scalar_one()
    assert asset.hostname == "good-host"
    assert asset.operating_system == "Debian"


# --- Service Creation ---

def test_service_created(db_session, inventory_service, scan_job):
    svc = ParsedService(port=22, protocol="tcp", service_name="ssh", product="OpenSSH", version="8.9")
    host = ParsedHost(ipv4="10.0.1.1", services=[svc])
    pkg = _make_package(scan_job.id, [host])

    inventory_service.process_assessment_package(pkg)

    asset = db_session.execute(select(Asset).where(Asset.ipv4 == "10.0.1.1")).scalar_one()
    service = db_session.execute(
        select(NetworkService).where(NetworkService.asset_id == asset.id, NetworkService.port == 22)
    ).scalar_one()
    assert service.service_name == "ssh"
    assert service.product == "OpenSSH"
    assert service.version == "8.9"


# --- Service Reuse & Metadata Update ---

def test_service_reused_and_updated(db_session, inventory_service, scan_job, target):
    # Pre-create asset + service
    asset = Asset(ipv4="10.0.1.2")
    db_session.add(asset)
    db_session.flush()
    svc = NetworkService(asset_id=asset.id, port=80, protocol="tcp", service_name="http", product="Apache", version="2.4")
    db_session.add(svc)
    db_session.flush()

    parsed_svc = ParsedService(port=80, protocol="tcp", service_name="http", product="Apache", version="2.4.58")
    host = ParsedHost(ipv4="10.0.1.2", services=[parsed_svc])
    pkg = _make_package(scan_job.id, [host])

    inventory_service.process_assessment_package(pkg)

    db_session.expire_all()
    services = db_session.execute(
        select(NetworkService).where(NetworkService.asset_id == asset.id)
    ).scalars().all()
    assert len(services) == 1
    assert services[0].version == "2.4.58"


# --- Vulnerability Creation ---

def test_vulnerability_created(db_session, inventory_service, scan_job):
    vuln = ParsedVulnerability(name="CVE-Test", severity_score=7.5, severity_rating="High", cve="CVE-2024-0001")
    svc = ParsedService(port=443, protocol="tcp", service_name="https", vulnerabilities=[vuln])
    host = ParsedHost(ipv4="10.0.2.1", services=[svc])
    pkg = _make_package(scan_job.id, [host])

    inventory_service.process_assessment_package(pkg)

    v = db_session.execute(select(Vulnerability).where(Vulnerability.cve == "CVE-2024-0001")).scalar_one()
    assert v.name == "CVE-Test"
    assert v.severity_rating == "High"


# --- Vulnerability Reuse (with CVE) ---

def test_vulnerability_reused_with_cve(db_session, inventory_service, scan_job, target):
    existing_v = Vulnerability(name="KnownVuln", severity_score=5.0, severity_rating="Medium", cve="CVE-2024-9999")
    db_session.add(existing_v)
    db_session.flush()

    vuln = ParsedVulnerability(name="KnownVuln", severity_score=5.0, severity_rating="Medium", cve="CVE-2024-9999")
    svc = ParsedService(port=80, protocol="tcp", service_name="http", vulnerabilities=[vuln])
    host = ParsedHost(ipv4="10.0.2.2", services=[svc])
    pkg = _make_package(scan_job.id, [host])

    inventory_service.process_assessment_package(pkg)

    count = db_session.execute(select(func.count(Vulnerability.id)).where(Vulnerability.cve == "CVE-2024-9999")).scalar()
    assert count == 1


# --- Duplicate Prevention: NULL CVE ---

def test_vulnerability_duplicate_prevention_null_cve(db_session, inventory_service, scan_job, target):
    existing_v = Vulnerability(name="MiscConfig", severity_score=3.0, severity_rating="Low", cve=None)
    db_session.add(existing_v)
    db_session.flush()

    vuln = ParsedVulnerability(name="MiscConfig", severity_score=3.0, severity_rating="Low", cve=None)
    svc = ParsedService(port=8080, protocol="tcp", service_name="http-alt", vulnerabilities=[vuln])
    host = ParsedHost(ipv4="10.0.2.3", services=[svc])
    pkg = _make_package(scan_job.id, [host])

    inventory_service.process_assessment_package(pkg)

    count = db_session.execute(
        select(func.count(Vulnerability.id)).where(Vulnerability.name == "MiscConfig", Vulnerability.cve.is_(None))
    ).scalar()
    assert count == 1


# --- ScanFinding Creation ---

def test_scan_finding_created(db_session, inventory_service, scan_job):
    vuln = ParsedVulnerability(name="TestFinding", severity_score=4.0, severity_rating="Medium", cve="CVE-2024-1234")
    svc = ParsedService(port=22, protocol="tcp", service_name="ssh", vulnerabilities=[vuln])
    host = ParsedHost(ipv4="10.0.3.1", services=[svc])
    pkg = _make_package(scan_job.id, [host])

    inventory_service.process_assessment_package(pkg)

    findings = db_session.execute(select(ScanFinding).where(ScanFinding.scan_id == scan_job.id)).scalars().all()
    assert len(findings) == 1
    assert findings[0].vulnerability_id is not None
    assert findings[0].service_id is not None


# --- ScanFinding Without Vulnerability ---

def test_scan_finding_service_only(db_session, inventory_service, scan_job):
    """Service without vulns should still create a finding linking scan + asset + service."""
    svc = ParsedService(port=53, protocol="udp", service_name="dns")
    host = ParsedHost(ipv4="10.0.3.2", services=[svc])
    pkg = _make_package(scan_job.id, [host])

    inventory_service.process_assessment_package(pkg)

    findings = db_session.execute(select(ScanFinding).where(ScanFinding.scan_id == scan_job.id)).scalars().all()
    assert len(findings) == 1
    assert findings[0].vulnerability_id is None
    assert findings[0].service_id is not None


# --- ScanFinding Duplicate Prevention ---

def test_scan_finding_idempotent(db_session, inventory_service, scan_job, target):
    """Processing the same package twice must not create duplicate findings."""
    vuln = ParsedVulnerability(name="DupFinding", severity_score=6.0, severity_rating="Medium", cve="CVE-2024-5555")
    svc = ParsedService(port=443, protocol="tcp", service_name="https", vulnerabilities=[vuln])
    host = ParsedHost(ipv4="10.0.4.1", services=[svc])

    # Process once
    pkg1 = _make_package(scan_job.id, [host])
    inventory_service.process_assessment_package(pkg1)

    # Reset scan_job status so processing is allowed again
    scan_job.status = ScanStatus.RUNNING
    db_session.flush()

    # Process again with identical data
    pkg2 = _make_package(scan_job.id, [host])
    inventory_service.process_assessment_package(pkg2)

    findings = db_session.execute(select(ScanFinding).where(ScanFinding.scan_id == scan_job.id)).scalars().all()
    assert len(findings) == 1


# --- Scan Status Transition to COMPLETED ---

def test_scan_status_completed(db_session, inventory_service, scan_job):
    host = ParsedHost(ipv4="10.0.5.1")
    pkg = _make_package(scan_job.id, [host])

    inventory_service.process_assessment_package(pkg)

    db_session.expire_all()
    updated = db_session.execute(select(ScanJob).where(ScanJob.id == scan_job.id)).scalar_one()
    assert updated.status == ScanStatus.COMPLETED
    assert updated.completed_at is not None


# --- Atomic Rollback on Failure ---

def test_rollback_on_failure(db_session, inventory_service, scan_job):
    """If processing fails mid-transaction, no partial data should persist."""
    vuln = ParsedVulnerability(name="RollbackTest", severity_score=1.0, severity_rating="Low")
    svc = ParsedService(port=80, protocol="tcp", service_name="http", vulnerabilities=[vuln])
    host = ParsedHost(ipv4="10.0.6.1", services=[svc])
    pkg = _make_package(scan_job.id, [host])

    # Patch _create_finding_if_not_exists to raise after asset/service/vuln are created
    with patch.object(inventory_service, "_create_finding_if_not_exists", side_effect=RuntimeError("simulated failure")):
        with pytest.raises(RuntimeError, match="simulated failure"):
            inventory_service.process_assessment_package(pkg)

    # After rollback, no assets should exist from this transaction
    count = db_session.execute(select(func.count(Asset.id)).where(Asset.ipv4 == "10.0.6.1")).scalar()
    assert count == 0


# --- Scan Status Transition to FAILED ---

def test_scan_status_failed_after_error(db_session, inventory_service, scan_job):
    """Scan transitions to FAILED after a processing error."""
    scan_id = scan_job.id
    host = ParsedHost(ipv4="10.0.7.1")
    pkg = _make_package(scan_id, [host])

    with patch.object(inventory_service, "_upsert_asset", side_effect=RuntimeError("db error")):
        with pytest.raises(RuntimeError, match="db error"):
            inventory_service.process_assessment_package(pkg)

    updated = db_session.execute(select(ScanJob).where(ScanJob.id == scan_id)).scalar_one()
    assert updated.status == ScanStatus.FAILED
    assert updated.failure_reason is not None


# --- CVE Normalization ---

def test_cve_normalization(db_session, inventory_service, scan_job):
    """Verify that CVEs are normalized to uppercase and stripped, preventing duplicates."""
    # First vuln with lowercase and trailing space CVE
    v1 = ParsedVulnerability(name="CVE-Test", severity_score=7.0, severity_rating="High", cve=" cve-2024-0002 ")
    s1 = ParsedService(port=443, protocol="tcp", service_name="https", vulnerabilities=[v1])
    h1 = ParsedHost(ipv4="10.0.8.1", services=[s1])
    pkg1 = _make_package(scan_job.id, [h1])
    inventory_service.process_assessment_package(pkg1)

    # Re-enable scan_job for reuse
    scan_job.status = ScanStatus.RUNNING
    db_session.flush()

    # Second vuln with standard uppercase CVE
    v2 = ParsedVulnerability(name="CVE-Test", severity_score=7.0, severity_rating="High", cve="CVE-2024-0002")
    s2 = ParsedService(port=443, protocol="tcp", service_name="https", vulnerabilities=[v2])
    h2 = ParsedHost(ipv4="10.0.8.1", services=[s2])
    pkg2 = _make_package(scan_job.id, [h2])
    inventory_service.process_assessment_package(pkg2)

    # Verify that only one vulnerability record is created and it has the normalized CVE
    v = db_session.execute(select(Vulnerability).where(Vulnerability.name == "CVE-Test")).scalar_one()
    assert v.cve == "CVE-2024-0002"

    count = db_session.execute(select(func.count(Vulnerability.id)).where(Vulnerability.name == "CVE-Test")).scalar()
    assert count == 1


# --- Duplicate Hosts in One Package ---

def test_duplicate_hosts_in_package(db_session, inventory_service, scan_job):
    """Verify that duplicate host entries in the same package are handled without creating duplicate assets."""
    h1 = ParsedHost(ipv4="10.0.9.1", hostname="host-first", operating_system="Linux")
    h2 = ParsedHost(ipv4="10.0.9.1", hostname="host-second", operating_system="Linux Kernel")
    pkg = _make_package(scan_job.id, [h1, h2])

    inventory_service.process_assessment_package(pkg)

    # Verify only one asset is created and it has the last-wins values
    asset = db_session.execute(select(Asset).where(Asset.ipv4 == "10.0.9.1")).scalar_one()
    assert asset.hostname == "host-second"
    assert asset.operating_system == "Linux Kernel"

    count = db_session.execute(select(func.count(Asset.id)).where(Asset.ipv4 == "10.0.9.1")).scalar()
    assert count == 1


# --- Duplicate Services in One Package ---

def test_duplicate_services_in_package(db_session, inventory_service, scan_job):
    """Verify that duplicate service entries in the same host package are handled without creating duplicate services."""
    s1 = ParsedService(port=80, protocol="tcp", service_name="http", product="Apache")
    s2 = ParsedService(port=80, protocol="tcp", service_name="http", product="Apache HTTPD")
    h = ParsedHost(ipv4="10.0.10.1", services=[s1, s2])
    pkg = _make_package(scan_job.id, [h])

    inventory_service.process_assessment_package(pkg)

    asset = db_session.execute(select(Asset).where(Asset.ipv4 == "10.0.10.1")).scalar_one()
    services = db_session.execute(
        select(NetworkService).where(NetworkService.asset_id == asset.id)
    ).scalars().all()

    # Verify only one service is created and it has the last-wins values
    assert len(services) == 1
    assert services[0].product == "Apache HTTPD"


# --- Duplicate Findings in One Package ---

def test_duplicate_findings_in_package(db_session, inventory_service, scan_job):
    """Verify that duplicate vulnerability/finding entries in the same service package are handled without creating duplicate findings."""
    v1 = ParsedVulnerability(name="DupFinding", severity_score=6.0, severity_rating="Medium", cve="CVE-2024-5555")
    v2 = ParsedVulnerability(name="DupFinding", severity_score=6.0, severity_rating="Medium", cve="CVE-2024-5555")
    s = ParsedService(port=443, protocol="tcp", service_name="https", vulnerabilities=[v1, v2])
    h = ParsedHost(ipv4="10.0.11.1", services=[s])
    pkg = _make_package(scan_job.id, [h])

    inventory_service.process_assessment_package(pkg)

    findings = db_session.execute(select(ScanFinding).where(ScanFinding.scan_id == scan_job.id)).scalars().all()
    assert len(findings) == 1

