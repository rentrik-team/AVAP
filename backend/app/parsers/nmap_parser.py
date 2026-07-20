import logging
import xml.etree.ElementTree as ET  # nosec B405 -- XXE-safe, see call-site comment below
from pathlib import Path

from app.core.enums import ScannerType
from app.core.exceptions import ParserException
from app.parsers.base_parser import BaseParser
from app.parsers.models import AssessmentPackage, ParsedHost, ParsedService
from app.scanners.scan_artifact import ScanArtifact

logger = logging.getLogger(__name__)


class NmapParser(BaseParser):
    """Secure parser for Nmap XML output files."""

    def parse(self, artifact: ScanArtifact) -> AssessmentPackage:
        """Parse Nmap XML output from the given artifact.

        Args:
            artifact: The ScanArtifact containing Nmap results.

        Returns:
            A populated AssessmentPackage.
        """
        if not artifact.output_path:
            raise ParserException("Scan artifact has no output path specified.")

        output_path = Path(artifact.output_path)
        if not output_path.exists():
            raise ParserException(f"Nmap output file not found at: {output_path}")

        logger.info(
            "Parsing Nmap XML output",
            extra={"scan_id": str(artifact.scan_id), "file_path": str(output_path)},
        )

        try:
            # Secure XML parsing: xml.etree.ElementTree's bundled expat parser
            # never resolves external entities (XXE-safe by default) and, on all
            # currently supported CPython versions, rejects entity-expansion
            # ("billion laughs") attacks via its built-in amplification limit.
            # No custom parser configuration or third-party library is required.
            tree = ET.parse(output_path)  # noqa: S314 # nosec B314 -- justified above, stdlib ET is XXE-safe
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(
                f"XML parse error in Nmap output: {e}",
                extra={"scan_id": str(artifact.scan_id), "file_path": str(output_path)},
            )
            raise ParserException(f"Failed to parse Nmap XML report: {e}") from e
        except Exception as e:
            logger.exception(
                f"Unexpected error reading Nmap output file: {e}",
                extra={"scan_id": str(artifact.scan_id)},
            )
            raise ParserException(f"Failed to read Nmap output file: {e}") from e

        parsed_hosts: list[ParsedHost] = []

        # Parse every <host> element in the XML
        for host_node in root.findall("host"):
            # 1. Find IPv4 address
            ipv4_addr = None
            for addr_node in host_node.findall("address"):
                if addr_node.get("addrtype") == "ipv4":
                    ipv4_addr = addr_node.get("addr")
                    break

            # If no IP, we skip or use a placeholder (Nmap should always
            # provide an IP for a host)
            if not ipv4_addr:
                logger.warning(
                    "Skipping host element with missing IPv4 address in Nmap report",
                    extra={"scan_id": str(artifact.scan_id)},
                )
                continue

            # 2. Find status
            status_node = host_node.find("status")
            if status_node is not None and status_node.get("state") != "up":
                # Only parse hosts that are up
                continue

            # 3. Find Hostname
            hostname = None
            hostnames_node = host_node.find("hostnames")
            if hostnames_node is not None:
                hostname_node = hostnames_node.find("hostname")
                if hostname_node is not None:
                    hostname = hostname_node.get("name")

            # 4. Find OS Match
            os_name = None
            os_node = host_node.find("os")
            if os_node is not None:
                osmatch_node = os_node.find("osmatch")
                if osmatch_node is not None:
                    os_name = osmatch_node.get("name")

            # 5. Parse Services / Open Ports
            parsed_services: list[ParsedService] = []
            ports_node = host_node.find("ports")
            if ports_node is not None:
                for port_node in ports_node.findall("port"):
                    # Check port state
                    state_node = port_node.find("state")
                    if state_node is not None and state_node.get("state") != "open":
                        # We only extract open ports/services
                        continue

                    port_id_str = port_node.get("portid")
                    protocol = port_node.get("protocol")
                    if not port_id_str or not protocol:
                        continue

                    try:
                        port_id = int(port_id_str)
                    except ValueError:
                        continue

                    service_name = "unknown"
                    product = None
                    version = None
                    extra_info = None

                    service_node = port_node.find("service")
                    if service_node is not None:
                        service_name = service_node.get("name", "unknown")
                        product = service_node.get("product")
                        version = service_node.get("version")
                        extra_info = service_node.get("extrainfo")

                    parsed_services.append(
                        ParsedService(
                            port=port_id,
                            protocol=protocol.lower(),
                            service_name=service_name,
                            product=product,
                            version=version,
                            extra_info=extra_info,
                            # Nmap port scanner doesn't report vulnerabilities
                            vulnerabilities=[],
                        )
                    )

            parsed_hosts.append(
                ParsedHost(
                    ipv4=ipv4_addr,
                    hostname=hostname,
                    operating_system=os_name,
                    services=parsed_services,
                )
            )

        # Extract execution metadata
        execution_metadata = {}
        scanner_version = root.get("version")
        if scanner_version:
            execution_metadata["scanner_version"] = scanner_version

        args = root.get("args")
        if args:
            execution_metadata["arguments"] = args

        return AssessmentPackage(
            scan_id=artifact.scan_id,
            scanner_type=ScannerType.NMAP,
            parsed_hosts=parsed_hosts,
            execution_metadata=execution_metadata,
        )
