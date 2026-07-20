import os
import tempfile
import uuid
from pathlib import Path

import pytest

from app.core.enums import ExecutionStatus, ScannerType
from app.parsers.openvas_parser import OpenVASParser
from app.scanners.scan_artifact import ScanArtifact


@pytest.fixture
def mock_openvas_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<report id="scan_123">
  <target>192.168.1.5</target>
  <results>
    <result id="res_1">
      <host>192.168.1.5</host>
      <port>22/tcp</port>
      <name>SSH Weak Algorithms</name>
      <severity>4.3</severity>
      <description>The remote SSH service supports weak ciphers.</description>
      <nvt>
        <name>SSH Weak Algorithms Detected</name>
        <cve>CVE-2023-1111</cve>
        <refs>
          <ref id="https://nvd.nist.gov/vuln/detail/CVE-2023-1111"/>
        </refs>
      </nvt>
    </result>
    <result id="res_2">
      <host>192.168.1.5</host>
      <port>80/tcp</port>
      <name>Apache Version Leak</name>
      <severity>7.5</severity>
      <description>Apache discloses version info in HTTP headers.</description>
      <nvt>
        <cve>nocve</cve>
      </nvt>
    </result>
  </results>
</report>
"""


def test_openvas_parser_success(mock_openvas_xml):
    with tempfile.NamedTemporaryFile(
        suffix=".xml", mode="w", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(mock_openvas_xml)
        tmp_path = Path(tmp.name)

    try:
        artifact = ScanArtifact(
            scan_id=uuid.uuid4(),
            scanner_type=ScannerType.OPENVAS,
            execution_status=ExecutionStatus.SUCCESS,
            output_path=tmp_path,
        )

        parser = OpenVASParser()
        package = parser.parse(artifact)

        assert package.scanner_type == ScannerType.OPENVAS
        assert len(package.parsed_hosts) == 1

        host = package.parsed_hosts[0]
        assert host.ipv4 == "192.168.1.5"

        # Open ports (22 and 80)
        assert len(host.services) == 2

        service_22 = next(s for s in host.services if s.port == 22)
        assert service_22.protocol == "tcp"
        assert len(service_22.vulnerabilities) == 1

        vuln_22 = service_22.vulnerabilities[0]
        assert vuln_22.name == "SSH Weak Algorithms Detected"  # NVT name override
        assert vuln_22.severity_score == 4.3
        assert vuln_22.severity_rating == "Medium"
        assert vuln_22.cve == "CVE-2023-1111"
        assert "https://nvd.nist.gov/vuln/detail/CVE-2023-1111" in vuln_22.references

        service_80 = next(s for s in host.services if s.port == 80)
        assert service_80.protocol == "tcp"
        assert len(service_80.vulnerabilities) == 1

        vuln_80 = service_80.vulnerabilities[0]
        assert vuln_80.name == "Apache Version Leak"
        assert vuln_80.severity_score == 7.5
        assert vuln_80.severity_rating == "High"
        assert vuln_80.cve is None  # nocve should map to None

    finally:
        os.unlink(tmp_path)


def test_openvas_severity_mapping():
    parser = OpenVASParser()
    assert parser._map_cvss_to_severity_rating(0.0) == "None"
    assert parser._map_cvss_to_severity_rating(2.5) == "Low"
    assert parser._map_cvss_to_severity_rating(5.5) == "Medium"
    assert parser._map_cvss_to_severity_rating(8.0) == "High"
    assert parser._map_cvss_to_severity_rating(9.8) == "Critical"
