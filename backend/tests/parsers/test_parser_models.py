import pytest
from pydantic import ValidationError
import uuid

from app.core.enums import ScannerType
from app.parsers.models import AssessmentPackage, ParsedHost, ParsedService, ParsedVulnerability


def test_parsed_vulnerability_validation():
    # Valid model
    vuln = ParsedVulnerability(
        name="SQL Injection",
        severity_score=9.8,
        severity_rating="CRITICAL",
        description="SQL injection in login parameter",
        cve="CVE-2023-9999",
        port=80,
        protocol="tcp",
        references=["http://example.com/ref"]
    )
    assert vuln.name == "SQL Injection"
    assert vuln.severity_score == 9.8
    assert vuln.severity_rating == "Critical"  # Validator should title case it
    assert vuln.cve == "CVE-2023-9999"

    # Invalid severity score (too high)
    with pytest.raises(ValidationError):
        ParsedVulnerability(name="SQL Injection", severity_score=11.0)

    # Invalid port (out of bounds)
    with pytest.raises(ValidationError):
        ParsedVulnerability(name="SQL Injection", port=70000)

    # Fallback for invalid severity rating
    vuln_bad_rating = ParsedVulnerability(
        name="Weak SSL",
        severity_score=4.0,
        severity_rating="UNRECOGNIZED_RATING"
    )
    assert vuln_bad_rating.severity_rating == "None"


def test_parsed_service_validation():
    # Valid
    service = ParsedService(
        port=443,
        protocol="tcp",
        service_name="https",
        product="nginx",
        version="1.18.0",
        vulnerabilities=[]
    )
    assert service.port == 443
    assert service.protocol == "tcp"

    # Out of bounds port
    with pytest.raises(ValidationError):
        ParsedService(port=0, protocol="tcp")


def test_assessment_package_validation():
    scan_id = uuid.uuid4()
    package = AssessmentPackage(
        scan_id=scan_id,
        scanner_type=ScannerType.NMAP,
        parsed_hosts=[
            ParsedHost(
                ipv4="192.168.1.1",
                hostname="router.local",
                services=[
                    ParsedService(port=80, protocol="tcp")
                ]
            )
        ]
    )
    assert package.scan_id == scan_id
    assert package.scanner_type == ScannerType.NMAP
    assert len(package.parsed_hosts) == 1
    assert package.parsed_hosts[0].ipv4 == "192.168.1.1"
