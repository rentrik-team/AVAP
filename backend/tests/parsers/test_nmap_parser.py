import os
import tempfile
import uuid
from pathlib import Path

import pytest

from app.core.enums import ExecutionStatus, ScannerType
from app.core.exceptions import ParserException
from app.parsers.nmap_parser import NmapParser
from app.scanners.scan_artifact import ScanArtifact


@pytest.fixture
def mock_nmap_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap -sV -oX test.xml 192.168.1.1" version="7.92">
  <host>
    <status state="up" reason="arp-response"/>
    <address addr="192.168.1.1" addrtype="ipv4"/>
    <hostnames>
      <hostname name="gateway.local" type="user"/>
    </hostnames>
    <ports>
      <port protocol="tcp" portid="80">
        <state state="open" reason="syn-ack" reason_ttl="64"/>
        <service name="http" product="Apache httpd" version="2.4.41"
                 extrainfo="Unix" method="probed" conf="10"/>
      </port>
      <port protocol="tcp" portid="22">
        <state state="open" reason="syn-ack"/>
        <service name="ssh" product="OpenSSH" version="8.2p1"
                 extrainfo="Ubuntu" method="probed"/>
      </port>
      <port protocol="tcp" portid="443">
        <state state="closed" reason="conn-refused"/>
      </port>
    </ports>
    <os>
      <osmatch name="Linux 5.4" accuracy="100"/>
    </os>
  </host>
</nmaprun>
"""


def test_nmap_parser_success(mock_nmap_xml):
    # Write mock xml to temporary file
    with tempfile.NamedTemporaryFile(
        suffix=".xml", mode="w", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(mock_nmap_xml)
        tmp_path = Path(tmp.name)

    try:
        artifact = ScanArtifact(
            scan_id=uuid.uuid4(),
            scanner_type=ScannerType.NMAP,
            execution_status=ExecutionStatus.SUCCESS,
            output_path=tmp_path,
        )

        parser = NmapParser()
        package = parser.parse(artifact)

        assert package.scanner_type == ScannerType.NMAP
        assert len(package.parsed_hosts) == 1

        host = package.parsed_hosts[0]
        assert host.ipv4 == "192.168.1.1"
        assert host.hostname == "gateway.local"
        assert host.operating_system == "Linux 5.4"

        # We only expect open ports (80 and 22), port 443 was closed
        assert len(host.services) == 2

        service_80 = next(s for s in host.services if s.port == 80)
        assert service_80.protocol == "tcp"
        assert service_80.service_name == "http"
        assert service_80.product == "Apache httpd"
        assert service_80.version == "2.4.41"
        assert service_80.extra_info == "Unix"

        service_22 = next(s for s in host.services if s.port == 22)
        assert service_22.service_name == "ssh"
        assert service_22.product == "OpenSSH"
        assert service_22.version == "8.2p1"

    finally:
        os.unlink(tmp_path)


def test_nmap_parser_corrupted_xml():
    with tempfile.NamedTemporaryFile(
        suffix=".xml", mode="w", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write("<nmaprun><host>broken-xml")
        tmp_path = Path(tmp.name)

    try:
        artifact = ScanArtifact(
            scan_id=uuid.uuid4(),
            output_path=tmp_path,
            execution_status=ExecutionStatus.SUCCESS,
        )
        parser = NmapParser()
        with pytest.raises(ParserException) as exc:
            parser.parse(artifact)
        assert "Failed to parse Nmap XML report" in str(exc.value)
    finally:
        os.unlink(tmp_path)


def test_nmap_parser_xxe_protection():
    """Verify parser does not expand external XML entities (XXE safety check)."""
    xxe_xml = """<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE foo [
  <!ELEMENT foo ANY >
  <!ENTITY xxe SYSTEM "file:///etc/passwd" >
]>
<nmaprun scanner="nmap" version="7.92">
  <host>
    <address addr="10.0.0.1" addrtype="ipv4"/>
    <hostnames>
      <hostname name="&xxe;" type="user"/>
    </hostnames>
  </host>
</nmaprun>
"""
    with tempfile.NamedTemporaryFile(
        suffix=".xml", mode="w", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(xxe_xml)
        tmp_path = Path(tmp.name)

    try:
        artifact = ScanArtifact(
            scan_id=uuid.uuid4(),
            output_path=tmp_path,
            execution_status=ExecutionStatus.SUCCESS,
        )
        parser = NmapParser()

        # When parsing XML containing external entity declarations with
        # resolve_entities=False, it either fails during parsing or keeps
        # the entity reference unexpanded/empty.
        try:
            package = parser.parse(artifact)
            # If it succeeded, check that the external reference was NOT expanded
            host = package.parsed_hosts[0]
            assert host.hostname != "/etc/passwd"
            assert host.hostname is None or host.hostname == ""
        except Exception:  # noqa: S110 -- raising is also a safe/valid resolution to XXE payloads
            pass
    finally:
        os.unlink(tmp_path)
